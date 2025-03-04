import os
import threading
import pandas as pd
from flask import Flask, render_template, redirect, url_for, flash
# Import your scraper functions (perform_scraping, etc.)
from google_maps_scraper import perform_scraping  # Replace with your actual file

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this in production!

CSV_FILE = "google_maps_results.csv"

scraping_in_progress = False  # Global flag

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
    return render_template('index.html', data=data, scraping_in_progress=scraping_in_progress)

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

if __name__ == '__main__':
    app.run(debug=True)