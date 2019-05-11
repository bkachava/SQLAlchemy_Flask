import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///../Resources/hawaii.sqlite?check_same_thread=False")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the database
session = Session(engine)

# Flask Setup
app = Flask(__name__)

def calcyearago():
    # Calculate the date 1 year ago from the last data point in the database
    last_point = session.query(func.max(Measurement.date)).\
        order_by(func.max(Measurement.date).desc()).first()
    last_year, last_month, last_day = last_point[0].split("-")
    last_date = dt.date(int(last_year), int(last_month), int(last_day))
    year_ago = last_date - dt.timedelta(days=366)

    return (year_ago)

def validate(year, month, day):
    # Verify if the date provided by the user is valid
    correctDate = None
    newDate = dt.date(2017, 1 ,31)
    try:
        newDate = dt.datetime(int(year), int(month), int(day))
        correctDate = True
    except ValueError:
        correctDate = False

    return(correctDate)


# Flask Routes
@app.route("/")
def welcome():
    """List all available api routes"""
    return (
        f"<html lang=\"en-us\">"
        f"<head>"
        f"<meta charset=\"UTF-8\">"
        f"<title>SQL Alchemy and Flask Assignment</title>"
        f"<style>\n"
        f"h1 {{\n"
        f"margin-bottom: 15px;\n"
        f"font-size: 30px;\n"
        f"color: white;\n"
        f"text-align: center;\n"
        f"background-color: rgb(15, 66, 128); \n}}\n"
        f"h2 {{\n"
        f"font-size: 20px;\n"
        f"color: rgb(28, 118, 230);\n}}\n"
        f"ul {{\n"
        f"font-size: 20px;\n"
        f"border-style: double;\n"
        f"border-width: 3px;\n"
        f"list-style-position: inside; \n}}\n"
        f"</style>"
        f"</head>"
        f"<body>"
        f"<h1>Step 2 - Climate API</h1>"
        f"<h2>Available Routes:</h2>"
        f"<ul><br>"
        f"<li><a href='/api/v1.0/precipitation'>Precipitation data</a>"
        f"&nbsp;&nbsp;<small>With this option you can retrieve the last 12 months of precipitation data</small></li><p></p>"
        f"<li><a href='/api/v1.0/stations'>Stations</a>"
        f"&nbsp;&nbsp;<small>Use this option to obtain the list of stations from the dataset</small></li><p></p>"        
        f"<li><a href='/api/v1.0/tobs'>Temperature data</a>"
        f"&nbsp;&nbsp;<small>Get the dates and temperature observations from a year</small></li><p></p>"
        f"<li>Temperatures - Start date:&nbsp;&nbsp;<small>For a given start date to the last point in the "
        f"dataset, here you can obtain the minimum, the average, and the maximum temperatures</small>"
        f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<a href='/api/v1.0/2016-08-23'>Example with start date 2016-08-23</a></li><br>"
        f"<li>Temperatures - Start/End dates:&nbsp;&nbsp;"
        f"<small>Within a range of dates get the minimum, the average, and the maximum temperatures</small>"
        f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"<a href='/api/v1.0/2016-08-23/2017-08-23'>Example with dates from 2016-08-23 to 2017-08-23</a></li>"
        f"<p></p></ul></body>"
        f"</html>" 
        )

@app.route("/api/v1.0/precipitation")
def prcponeyear():
    """Convert the query results to a Dictionary using date as the key and prcp as the value
        Return the JSON representation of your dictionary"""
    
    # Retrieve the last 12 months of precipitation data
    year_ago = calcyearago()
    
    # Perform a query to retrieve the data and precipitation scores
    prec_data = session.query(Measurement.date, Measurement.prcp, Measurement.station).\
        filter(Measurement.date > year_ago).all()

    # Define the dictionary with the data to be included in the JSON response file
    results = []
    for row in prec_data:
        prec_dict = {}
        prec_dict["date"] = row[0]
        prec_dict["prcp"] = row[1]
        prec_dict["station"] = row[2]
        results.append(prec_dict)

    return jsonify(results)


@app.route("/api/v1.0/stations")
def allstations():
    """Return a JSON list of stations from the dataset"""

    # Query all stations
    stat = session.query(Station.id, Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()

    # Define the dictionary with the data to be included in the JSON response file
    all_stations = []
    for row in stat:
        station_dict = {}
        station_dict["id"] = row[0]
        station_dict["station"] = row[1]
        station_dict["name"] = row[2].replace(",",";")
        station_dict["latitude"] = row[3]
        station_dict["longitude"] = row[4]
        station_dict["elevation"] = row[5]        
        all_stations.append(station_dict)

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def tobsoneyear():
    """Query for the dates and temperature observations from a year from the last data point
       Return a JSON list of Temperature Observations (tobs) for the previous year"""
    
    # Query the last 12 months of temperature observation data for 
    # the station with the highest number of temperature observations
    year_ago = calcyearago()
    tobs_one = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date > year_ago).all()

    # Define the dictionary with the data to be included in the JSON response file
    temp_lst = []
    for row in tobs_one:
        tobs_dict = {}
        tobs_dict["date"] = row[0]
        tobs_dict["tobs"] = row[1]
        temp_lst.append(tobs_dict)

    return jsonify(temp_lst)

@app.route("/api/v1.0/<start>")  
def start(start):
    """Return a JSON list of the minimum temperature, the average temperature, and 
       the max temperature for a given start date. Calculate TMIN, TAVG, and TMAX 
       for all dates greater than and equal to the start date"""

    # Code that might cause an exception
    try:
        year, month, day = start.split("-")
    except ValueError:
        # Notify the user in case the data is not valid
        return jsonify({"Error": f"Please check your start date {start}, it must be a valid date and have the following format YYYY-MM-DD."}), 404
    else:
        # Code to be ejecuted if the try block was successful
        if validate(year, month, day):

            # Query to get the temperatures with aggregates functions
            from_date = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                filter(Measurement.date >= start).all()

            # Define the dictionary with the data to be included in the JSON response file
            date_dict = {}
            date_dict["startdate"] = start
            date_dict["min"] = from_date[0][0]
            date_dict["average"] = round(float(from_date[0][1]),2)
            date_dict["max"] = from_date[0][2]

            return jsonify(date_dict)
        
        # Notify the user in case the data is not valid
        return jsonify({"Error": f"Please check your start date {start}, it must be a valid date and have the following format YYYY-MM-DD."}), 404

@app.route("/api/v1.0/<start>/<end>")  
def startend(start,end):
    """Return a JSON list of the minimum temperature, the average temperature, and 
       the max temperature for a given start-end date range. Calculate the TMIN, 
       TAVG, and TMAX for dates between the start and end date inclusive"""

    # Code that might cause an exception
    try:
        syear, smonth, sday = start.split("-")
        eyear, emonth, eday = end.split("-")
    except ValueError:
        # Notify the user in case the data is not valid
        return jsonify({"Error": f"Please check your dates: start {start} or end {end}. They must be valid and have the following format YYYY-MM-DD."}), 404
    else:
        # Code to be ejecuted if the try block was successful
        if validate(syear, smonth, sday) and validate(eyear, emonth, eday):
            # Query to get the temperatures with aggregates functions
            fromto_date = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                filter(Measurement.date >= start).filter(Measurement.date <= end).all()

            # Define the dictionary with the data to be included in the JSON response file
            date_dict = {}
            date_dict["startdate"] = start
            date_dict["enddate"] = end
            date_dict["min"] = fromto_date[0][0]
            date_dict["average"] = round(float(fromto_date[0][1]),2)
            date_dict["max"] = fromto_date[0][2]

            return jsonify(date_dict)
        
        # Notify the user in case the data is not valid
        return jsonify({"Error": f"Please check your dates: start {start} or end {end}. They must be valid and have the following format YYYY-MM-DD."}), 404

if __name__ == '__main__':
    app.run(debug=True)
