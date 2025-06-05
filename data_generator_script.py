import argparse
import math
import random
from datetime import datetime, timedelta

import pandas as pd


# Probability that a generated location (beyond initial center coordinates) becomes a depot
DEPOT_PROBABILITY = 0.10

PRODUCT_TYPES = ["Leafy", "Dairy", "Herbs", "Meat", "Fruit"]
PACKAGING_TYPES = ["Crate", "Box", "Pallet"]
CONTAMINATION_GROUPS = ["A", "B", "C"]
HANDLING_NOTES = ["Fragile", "Keep Upright", "None"]

# Vehicle capacity bounds
MIN_CAPACITY = 100
MAX_CAPACITY = 500

# Hour bounds for vehicle availability (24-hour clock)
HOURS_IN_DAY = 24  # 0 through 23

def _random_point_within_radius(lat_center, lon_center, radius_miles):
    """
    Return (latitude, longitude) randomly sampled within `radius_miles` miles of
    (lat_center, lon_center) using uniform spherical-cap sampling.
    """
    R_EARTH_MILES = 3958.8
    ang_rad = radius_miles / R_EARTH_MILES

    u = random.random()
    cos_theta = 1 - u * (1 - math.cos(ang_rad))
    theta = math.acos(cos_theta)
    bearing = random.uniform(0, 2 * math.pi)

    lat0 = math.radians(lat_center)
    lon0 = math.radians(lon_center)

    lat_new = math.asin(
        math.sin(lat0) * math.cos(theta) +
        math.cos(lat0) * math.sin(theta) * math.cos(bearing)
    )
    lon_new = lon0 + math.atan2(
        math.sin(bearing) * math.sin(theta) * math.cos(lat0),
        math.cos(theta) - math.sin(lat0) * math.sin(lat_new)
    )

    return math.degrees(lat_new), math.degrees(lon_new)


def _make_customer_fields():
    """
    Generate and return a dict of fully populated “customer” fields:
      - Demand_unit (1-25)
      - Product_Type (chosen from PRODUCT_TYPES)
      - Temp_Min, Temp_Max (based on product)
      - Ripeness_Date, Expiration_Date (MM/DD/YYYY)
      - Packaging_Type, Contamination_Group, Handling_Notes
      - Urgency_Score (0.00 - 1.00)
      - Time_Window_Start, Time_Window_End (random time slot)
    """
    ptype = random.choice(PRODUCT_TYPES)
    if ptype == "Leafy":
        tmin, tmax = (1, 7)
    elif ptype == "Dairy":
        tmin, tmax = (0, 4)
    elif ptype == "Herbs":
        tmin, tmax = (5, 10)
    elif ptype == "Meat":
        tmin, tmax = (-2, 0)
    else:  # Fruit
        tmin, tmax = (4, 8)

    demand = random.randint(1, 25)

    today = datetime.now().date()
    ripeness_offset = random.randint(0, 3)
    ripeness_date = today + timedelta(days=ripeness_offset)
    exp_offset = random.randint(2, 7)
    exp_date = ripeness_date + timedelta(days=exp_offset)

    packaging = random.choice(PACKAGING_TYPES)
    contam_grp = random.choice(CONTAMINATION_GROUPS)
    handling = random.choice(HANDLING_NOTES)
    urgency = round(random.random(), 2)

    tw_choice = random.choice(["morning", "afternoon", "evening"])
    if tw_choice == "morning":
        tw_start, tw_end = "08:00", "12:00"
    elif tw_choice == "afternoon":
        tw_start, tw_end = "12:00", "17:00"
    else:
        tw_start, tw_end = "17:00", "20:00"

    return {
        "Demand_unit": demand,
        "Product_Type": ptype,
        "Temp_Min": tmin,
        "Temp_Max": tmax,
        "Ripeness_Date": ripeness_date.strftime("%m/%d/%Y"),
        "Expiration_Date": exp_date.strftime("%m/%d/%Y"),
        "Packaging_Type": packaging,
        "Contamination_Group": contam_grp,
        "Handling_Notes": handling,
        "Urgency_Score": urgency,
        "Time_Window_Start": tw_start,
        "Time_Window_End": tw_end
    }


def generate_synthetic_locations(num_records, lat_center, lon_center, radius_miles):
    """
    Create a DataFrame with `num_records` synthetic location rows.

    - The first row (L001) is a fixed depot at exactly (lat_center, lon_center),
      with Depot_Flag = TRUE and fully populated fields (like a “customer”).
    - Among the remaining (num_records - 1) rows, each has a DEPOT_PROBABILITY
      chance to be flagged as an additional depot (Depot_Flag = TRUE). All rows—
      depots or customers—have their fields fully populated via _make_customer_fields().

    Returns: pandas.DataFrame with columns:
      Location_ID, Latitude, Longitude, Demand_unit, Depot_Flag, Product_Type,
      Temp_Min, Temp_Max, Ripeness_Date, Expiration_Date, Packaging_Type,
      Contamination_Group, Handling_Notes, Urgency_Score, Time_Window_Start, Time_Window_End
    """
    rows = []

    # 1) Fixed depot at exactly (lat_center, lon_center)
    depot_fields = _make_customer_fields()
    rows.append({
        "Location_ID": "L001",
        "Latitude": round(lat_center, 6),
        "Longitude": round(lon_center, 6),
        "Depot_Flag": "TRUE",
        **depot_fields
    })

    # 2) Generate the remaining (num_records - 1) rows
    for i in range(2, num_records + 1):
        loc_id = f"L{i:03d}"
        lat_rand, lon_rand = _random_point_within_radius(lat_center, lon_center, radius_miles)
        is_depot = (random.random() < DEPOT_PROBABILITY)

        customer_data = _make_customer_fields()
        rows.append({
            "Location_ID": loc_id,
            "Latitude": round(lat_rand, 6),
            "Longitude": round(lon_rand, 6),
            "Depot_Flag": "TRUE" if is_depot else "FALSE",
            **customer_data
        })

    return pd.DataFrame(rows)


def generate_synthetic_vehicles(all_locations_df):
    """
    Create a DataFrame of synthetic vehicle rows.

    - Number of vehicles is at least 30% of the total number of location rows (rounded up).
    - Each vehicle’s Start_Location is chosen randomly from any Location_ID
      where Depot_Flag == TRUE.
    - Each vehicle’s Capacity_boxes is a random integer between MIN_CAPACITY and MAX_CAPACITY.
    - Available_From is a random hour between 00:00 and 23:00.
    - Available_Until is a random hour between Available_From and 23:00.

    Returns: pandas.DataFrame with columns:
      Vehicle_ID, Capacity_boxes, Temp_Min, Temp_Max, Start_Location, Available_From, Available_Until
    """
    total_locations = len(all_locations_df)
    num_vehicles = math.ceil(0.30 * total_locations)
    if num_vehicles < 1:
        num_vehicles = 1

    depot_ids = all_locations_df.loc[all_locations_df["Depot_Flag"] == "TRUE", "Location_ID"].tolist()
    if not depot_ids:
        raise ValueError("No depot found in locations data; cannot generate vehicles.")

    rows = []
    for i in range(1, num_vehicles + 1):
        vid = f"V{i:03d}"
        cap = random.randint(MIN_CAPACITY, MAX_CAPACITY)
        # Random temperature band from three options
        tmin, tmax = random.choice([(-2, 10), (0, 8), (-5, 4)])

        # Random availability window anywhere in 24-hour clock
        start_hour = random.randint(0, HOURS_IN_DAY - 1)  # 0 through 23
        end_hour = random.randint(start_hour, HOURS_IN_DAY - 1)  # ≥ start_hour, ≤ 23

        available_from = f"{start_hour:02d}:00"
        available_until = f"{end_hour:02d}:00"

        start_loc = random.choice(depot_ids)
        rows.append({
            "Vehicle_ID": vid,
            "Capacity_boxes": cap,
            "Temp_Min": tmin,
            "Temp_Max": tmax,
            "Start_Location": start_loc,
            "Available_From": available_from,
            "Available_Until": available_until
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Generate two CSVs: locations.csv and vehicles.csv"
    )
    parser.add_argument(
        "--num_records", "-n", type=int, required=True,
        help="Total number of location rows to generate (including L001 as fixed depot)."
    )
    parser.add_argument(
        "--lat", type=float, required=True,
        help="Center latitude (decimal degrees) for the fixed depot (L001)."
    )
    parser.add_argument(
        "--lon", type=float, required=True,
        help="Center longitude (decimal degrees) for the fixed depot (L001)."
    )
    parser.add_argument(
        "--radius", type=float, required=True,
        help="Radius in miles around (lat, lon) to generate random location points."
    )
    parser.add_argument(
        "--locations_output", type=str, default="locations.csv",
        help="Filename for the locations CSV."
    )
    parser.add_argument(
        "--vehicles_output", type=str, default="vehicles.csv",
        help="Filename for the vehicles CSV."
    )
    args = parser.parse_args()

    # 1) Generate locations DataFrame
    df_loc = generate_synthetic_locations(
        num_records=args.num_records,
        lat_center=args.lat,
        lon_center=args.lon,
        radius_miles=args.radius
    )

    # 2) Save locations to CSV
    df_loc.to_csv(args.locations_output, index=False)
    print(f"Wrote {len(df_loc)} locations → {args.locations_output}")

    # 3) Generate vehicles DataFrame (≥30% of total location count)
    df_veh = generate_synthetic_vehicles(all_locations_df=df_loc)

    # 4) Save vehicles to CSV
    df_veh.to_csv(args.vehicles_output, index=False)
    print(f"Wrote {len(df_veh)} vehicles (30% of {len(df_loc)}) → {args.vehicles_output}")


if __name__ == "__main__":
    main()
