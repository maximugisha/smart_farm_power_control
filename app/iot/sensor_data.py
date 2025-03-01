import json
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from flask import current_app
import logging

from app import db
from app.models.power_usage import PowerReading, PowerSummary, EnergyRate
from app.models.device import Device
from app.models.notification import Notification

logger = logging.getLogger(__name__)

def process_sensor_data(device_id, data):
    """
    Process incoming sensor data

    Args:
        device_id (str): Device ID from IoT device
        data (dict): Sensor data

    Returns:
        bool: Success or failure
    """
    try:
        # Find the device
        device = Device.query.filter_by(device_id=device_id).first()
        if not device:
            logger.warning(f"Received data for unknown device: {device_id}")
            return False

        # Update device status
        device.last_updated = datetime.utcnow()
        if "status" in data:
            device.status = data["status"]

        # Update power state if provided
        if "power_state" in data:
            device.power_state = data["power_state"]

        # Create power reading if power data is provided
        if "power" in data:
            device.current_power = float(data["power"])

            # Create power reading record
            power_reading = PowerReading(
                device_id=device.id,
                power_usage=float(data["power"]),
                voltage=float(data.get("voltage", 0)),
                current=float(data.get("current", 0)),
                power_factor=float(data.get("power_factor", 0))
            )

            # If energy data is provided, use it
            if "energy" in data:
                power_reading.energy_consumed = float(data["energy"])

            db.session.add(power_reading)

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Error processing sensor data: {str(e)}")
        return False

def get_device_power_stats(device_id, period="day"):
    """
    Get power statistics for a device

    Args:
        device_id (int): Device ID in database
        period (str): Time period - "day", "week", or "month"

    Returns:
        dict: Power statistics
    """
    try:
        # Set the time range based on period
        now = datetime.utcnow()
        if period == "day":
            start_time = now - timedelta(days=1)
        elif period == "week":
            start_time = now - timedelta(weeks=1)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=1)

        # Query power readings
        readings = PowerReading.query.filter(
            PowerReading.device_id == device_id,
            PowerReading.timestamp >= start_time
        ).order_by(PowerReading.timestamp).all()

        if not readings:
            return {
                "device_id": device_id,
                "period": period,
                "total_readings": 0,
                "average_power": 0,
                "max_power": 0,
                "min_power": 0,
                "total_energy": 0,
                "readings": []
            }

        # Calculate statistics
        power_values = [r.power_usage for r in readings]
        avg_power = sum(power_values) / len(power_values)
        max_power = max(power_values)
        min_power = min(power_values)

        # Calculate total energy (kWh) - simple method
        total_energy = 0
        for i in range(1, len(readings)):
            # Time difference in hours
            time_diff = (readings[i].timestamp - readings[i-1].timestamp).total_seconds() / 3600
            # Average power between readings
            avg_power_between = (readings[i].power_usage + readings[i-1].power_usage) / 2
            # Energy in kWh = power (W) * time (h) / 1000
            energy = (avg_power_between * time_diff) / 1000
            total_energy += energy

        # Format readings for response
        formatted_readings = []
        for reading in readings:
            formatted_readings.append({
                "timestamp": reading.timestamp.isoformat(),
                "power": reading.power_usage,
                "voltage": reading.voltage,
                "current": reading.current
            })

        return {
            "device_id": device_id,
            "period": period,
            "total_readings": len(readings),
            "average_power": avg_power,
            "max_power": max_power,
            "min_power": min_power,
            "total_energy": total_energy,
            "readings": formatted_readings
        }

    except Exception as e:
        logger.error(f"Error getting device power stats: {str(e)}")
        return {
            "error": str(e)
        }

def generate_daily_power_summary():
    """
    Generate daily power summaries for all devices and farm-wide
    Should be run at the end of each day via scheduled task

    Returns:
        bool: Success or failure
    """
    try:
        # Get yesterday's date
        yesterday = datetime.utcnow().date() - timedelta(days=1)

        # Get all devices
        devices = Device.query.all()
        farm_total_energy = 0
        farm_peak_power = 0
        farm_cost_estimate = 0

        # Get current energy rate
        energy_rate = EnergyRate.query.filter(
            EnergyRate.valid_from <= yesterday,
            (EnergyRate.valid_to == None) | (EnergyRate.valid_to >= yesterday)
        ).first()

        rate_per_kwh = energy_rate.rate_per_kwh if energy_rate else 0.15  # Default to $0.15/kWh

        # Process each device
        for device in devices:
            # Get power readings for yesterday
            start_time = datetime.combine(yesterday, datetime.min.time())
            end_time = datetime.combine(yesterday, datetime.max.time())

            readings = PowerReading.query.filter(
                PowerReading.device_id == device.id,
                PowerReading.timestamp >= start_time,
                PowerReading.timestamp <= end_time
            ).all()

            if not readings:
                continue

            # Calculate total energy and peak power
            power_values = [r.power_usage for r in readings]
            peak_power = max(power_values)
            avg_power = sum(power_values) / len(power_values)

            # Calculate total energy (kWh)
            total_energy = 0
            for i in range(1, len(readings)):
                # Time difference in hours
                time_diff = (readings[i].timestamp - readings[i-1].timestamp).total_seconds() / 3600
                # Average power between readings
                avg_power_between = (readings[i].power_usage + readings[i-1].power_usage) / 2
                # Energy in kWh = power (W) * time (h) / 1000
                energy = (avg_power_between * time_diff) / 1000
                total_energy += energy

            # Calculate cost
            cost_estimate = total_energy * rate_per_kwh

            # Create device summary
            device_summary = PowerSummary(
                summary_type='daily',
                date=yesterday,
                total_energy=total_energy,
                peak_power=peak_power,
                average_power=avg_power,
                cost_estimate=cost_estimate,
                device_id=device.id
            )
            db.session.add(device_summary)

            # Update farm totals
            farm_total_energy += total_energy
            farm_peak_power = max(farm_peak_power, peak_power)
            farm_cost_estimate += cost_estimate

        # Create farm-wide summary
        farm_summary = PowerSummary(
            summary_type='daily',
            date=yesterday,
            total_energy=farm_total_energy,
            peak_power=farm_peak_power,
            average_power=0,  # Not meaningful for farm-wide
            cost_estimate=farm_cost_estimate,
            device_id=None  # No specific device
        )
        db.session.add(farm_summary)

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Error generating daily power summary: {str(e)}")
        db.session.rollback()
        return False

def get_farm_power_summary(user_id, period="day", start_date=None, end_date=None):
    """
    Get farm-wide power usage summary

    Args:
        user_id (int): User ID
        period (str): Time period - "day", "week", "month", "custom"
        start_date (datetime.date): Start date for custom period
        end_date (datetime.date): End date for custom period

    Returns:
        dict: Farm power summary
    """
    try:
        # Set date range based on period
        today = datetime.utcnow().date()

        if period == "day":
            start_date = today - timedelta(days=1)
            end_date = today
        elif period == "week":
            start_date = today - timedelta(weeks=1)
            end_date = today
        elif period == "month":
            start_date = today - timedelta(days=30)
            end_date = today
        elif period == "custom":
            if not start_date or not end_date:
                return {"error": "Start date and end date required for custom period"}
        else:
            start_date = today - timedelta(days=1)
            end_date = today

        # Get devices for this user
        devices = Device.query.filter_by(user_id=user_id).all()
        device_ids = [d.id for d in devices]

        # Get power summaries for all user's devices
        summaries = PowerSummary.query.filter(
            PowerSummary.device_id.in_(device_ids),
            PowerSummary.date >= start_date,
            PowerSummary.date < end_date,
            PowerSummary.summary_type == 'daily'
        ).all()

        # Aggregate data by date
        daily_data = {}
        for summary in summaries:
            date_str = summary.date.isoformat()
            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": date_str,
                    "total_energy": 0,
                    "cost_estimate": 0,
                    "peak_power": 0
                }

            daily_data[date_str]["total_energy"] += summary.total_energy
            daily_data[date_str]["cost_estimate"] += summary.cost_estimate
            daily_data[date_str]["peak_power"] = max(
                daily_data[date_str]["peak_power"],
                summary.peak_power
            )

        # Convert dictionary to list
        daily_summaries = list(daily_data.values())

        # Calculate totals for the period
        total_energy = sum(day["total_energy"] for day in daily_summaries)
        total_cost = sum(day["cost_estimate"] for day in daily_summaries)
        avg_daily_energy = total_energy / len(daily_summaries) if daily_summaries else 0

        # Get top energy consumers
        device_totals = {}
        for summary in summaries:
            if summary.device_id not in device_totals:
                device = Device.query.get(summary.device_id)
                device_totals[summary.device_id] = {
                    "device_id": summary.device_id,
                    "name": device.name if device else "Unknown Device",
                    "total_energy": 0,
                    "total_cost": 0
                }

            device_totals[summary.device_id]["total_energy"] += summary.total_energy
            device_totals[summary.device_id]["total_cost"] += summary.cost_estimate

        # Sort devices by energy consumption
        top_consumers = sorted(
            device_totals.values(),
            key=lambda x: x["total_energy"],
            reverse=True
        )

        return {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_energy": total_energy,
            "total_cost": total_cost,
            "avg_daily_energy": avg_daily_energy,
            "top_consumers": top_consumers[:5],  # Top 5 devices
            "daily_summaries": daily_summaries
        }

    except Exception as e:
        logger.error(f"Error getting farm power summary: {str(e)}")
        return {"error": str(e)}