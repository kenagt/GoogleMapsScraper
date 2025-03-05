import os
import threading
import pandas as pd
from flask import Flask, render_template, redirect, url_for, flash
# Import your scraper functions (perform_scraping, etc.)
from google_maps_scraper import perform_scraping  # Replace with your actual file
import json
# Charting imports
import plotly.graph_objects as go
import plotly.io as pio
pio.templates.default = "plotly_white"  # Or any other template you prefer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this in production!

CSV_FILE = "google_maps_results.csv"
JSON_FILE = "google_maps_results.json"

# Global variables for data and progress
scraping_in_progress = False  # Global flag
with open(JSON_FILE, 'r') as file:
    scraped_data = json.loads(file.read())

def read_csv_data(filename):
    """Reads CSV data and returns a list of dictionaries, handling empty files."""
    try:
        # Check if the file exists and is not empty
        if os.path.exists(filename) and os.stat(filename).st_size > 0:
            df = pd.read_csv(filename)
            return df.to_dict(orient='records')  # Convert rows to list of dicts
        else:
            # Return an empty list if the file is empty or doesn't exist
            return []
    except pd.errors.EmptyDataError:
        # Catch the EmptyDataError specifically and return an empty list
        print("CSV file is empty.")  # Optional: Log the event
        return []
    except FileNotFoundError:
        print("CSV file not found")
        return []
    except Exception as e:
        # Handle other potential errors
        print(f"Error reading CSV file: {e}")
        return []
    
@app.route('/')
def index():
    data = read_csv_data(CSV_FILE)
    rating_distribution_json = create_rating_distribution_chart()
    price_distribution_json = create_price_distribution_chart()
    return render_template('index.html', 
                           data=data, 
                           scraping_in_progress=scraping_in_progress,
                           rating_distribution_json=rating_distribution_json,
                            price_distribution_json=price_distribution_json,
                           )

@app.route('/start_scraping')
def start_scraping():
    global scraping_in_progress
    if not scraping_in_progress:
        scraping_in_progress = True
        flash("Scraping started. Please wait...", 'info')
        # Run scraping in a separate thread
        scraping_thread = threading.Thread(target=run_scraping)
        scraping_thread.daemon = True  # Allow app to exit even if thread is running
        scraping_thread.start()
    else:
        flash("Scraping is already in progress.", 'warning')
    return redirect(url_for('index'))

def run_scraping():
    """Wrapper function to run the scraping and update the flag."""
    global scraping_in_progress
    try:
        perform_scraping()  # Call your scraping function
        flash("Scraping finished!", 'success')
    except Exception as e:
        flash(f"Scraping failed: {str(e)}", 'danger')
        # Log the error (optional)
        app.logger.error("Scraping error:", exc_info=True)
    finally:
        scraping_in_progress = False  # Reset flag

# --- Chart creation functions ---
def create_rating_distribution_chart():
    """Creates a Plotly bar chart for rating distribution (1-5 stars)."""
    global scraped_data
    
    if not scraped_data:
        return "{}"  # Return empty JSON object
    
    ratings = filter(lambda p: p != "N/A", scraped_data)    
    ratings = [data['averageReviewScore'].replace(",", ".") for data in scraped_data if data['averageReviewScore'] != "N/A"]
    ratings = [round(float(data)) for data in ratings]
    
    if not ratings:
        return "{}"
    
    # Count occurrences of ratings 1 to 5
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating in ratings:
        if rating in counts:
            counts[rating] += 1
    
    labels = [str(key) + " Stars" for key in counts.keys()]
    counts_list = list(counts.values())
    
    fig = go.Figure(data=[go.Bar(x=labels, y=counts_list, marker_color='blue', text=counts_list, textposition='auto')])
    
    fig.update_layout(
        title="Hotel Rating Distribution",
        xaxis_title="Star Ratings",
        yaxis_title="Number of Hotels",
        template="plotly_white",
        showlegend=False,
        width=500,
        height=500,
    )
    return pio.to_json(fig)

def create_price_distribution_chart():
    """Creates a Plotly pie chart for price distribution."""
    global scraped_data
    
    if not scraped_data:
        return "{}"  # Return empty JSON object
     
    price_levels = filter(lambda p: p != "N/A", scraped_data)
    price_levels = [data['averageOtaPrice'] for data in scraped_data if data['averageOtaPrice'] != "N/A"]   
    price_levels = [round(float(data)) for data in price_levels]

    if not price_levels:
        return "{}"
    
    # Define price categories
    counts = {"Up to $300": 0, "$301 - $600": 0, "$601 - $900": 0, "Above $900": 0}
    
    for price in price_levels:
        if price <= 300:
            counts["Up to $300"] += 1
        elif price <= 600:
            counts["$301 - $600"] += 1
        elif price <= 900:
            counts["$601 - $900"] += 1
        else:
            counts["Above $900"] += 1
    
    labels_list = list(counts.keys())
    counts_list = list(counts.values())
    
    fig = go.Figure(data=[go.Pie(labels=labels_list, values=counts_list, hole=0.4, marker={'colors': ['green', 'blue', 'orange', 'red']})])
    
    fig.update_layout(
        title="Hotel Price Distribution",
        template="plotly_white",
        width=500,
        height=500,
    )
    
    return pio.to_json(fig)



if __name__ == '__main__':
    app.run(debug=True)