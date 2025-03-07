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
            return df.to_dict(
                orient='records')  # Convert rows to list of dicts
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
    market_positioning_json = create_market_positioning_chart()
    
    # Add initial amenity analysis with default hotel
    amenity_analysis_json = create_amenity_gap_analysis()

    return render_template(
        'index.html',
        data=data,
        scraping_in_progress=scraping_in_progress,
        rating_distribution_json=rating_distribution_json,
        price_distribution_json=price_distribution_json,
        market_positioning_json=market_positioning_json,
        amenity_analysis_json=amenity_analysis_json
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
    ratings = [
        data['averageReviewScore'].replace(",", ".") for data in scraped_data
        if data['averageReviewScore'] != "N/A"
    ]
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

    fig = go.Figure(data=[
        go.Bar(x=labels,
               y=counts_list,
               marker_color='blue',
               text=counts_list,
               textposition='auto')
    ])

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
    price_levels = [
        data['averageOtaPrice'] for data in scraped_data
        if data['averageOtaPrice'] != "N/A"
    ]
    price_levels = [round(float(data)) for data in price_levels]

    if not price_levels:
        return "{}"

    # Define price categories
    counts = {
        "Up to $300": 0,
        "$301 - $600": 0,
        "$601 - $900": 0,
        "Above $900": 0
    }

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

    fig = go.Figure(data=[
        go.Pie(labels=labels_list,
               values=counts_list,
               hole=0.4,
               marker={'colors': ['green', 'blue', 'orange', 'red']})
    ])

    fig.update_layout(
        title="Hotel Price Distribution",
        template="plotly_white",
        width=500,
        height=500,
    )

    return pio.to_json(fig)


def create_market_positioning_chart():
    """Creates a Plotly scatter plot for market positioning (price vs. quality)."""
    global scraped_data

    if not scraped_data:
        return "{}"  # Return empty JSON object

    # Extract price and rating data
    data_points = []
    for hotel in scraped_data:
        price = hotel['averageOtaPrice']
        rating = hotel['averageReviewScore']
        name = hotel['name']

        # Skip if any data is missing
        if price == "N/A" or rating == "N/A" or name == "N/A":
            continue

        try:
            price = float(price.replace(",", "."))
            rating = float(rating.replace(",", "."))
            data_points.append({
                "name": name,
                "price": price,
                "rating": rating
            })
        except (ValueError, TypeError):
            continue

    if not data_points:
        return "{}"

    # Create scatter plot
    names = [point["name"] for point in data_points]
    prices = [point["price"] for point in data_points]
    ratings = [point["rating"] for point in data_points]

    # Calculate average price and rating for quadrant lines
    avg_price = sum(prices) / len(prices)
    avg_rating = sum(ratings) / len(ratings)

    # Create scatter plot
    fig = go.Figure()

    # Add the data points
    fig.add_trace(
        go.Scatter(
            x=ratings,
            y=prices,
            mode='markers+text',
            marker=dict(size=12, color='blue', opacity=0.7),
            text=names,
            textposition="top center",
            hovertemplate=
            '<b>%{text}</b><br>Rating: %{x:.1f}<br>Price: $%{y:.2f}<extra></extra>'
        ))

    # Add quadrant lines
    fig.add_shape(type="line",
                  x0=avg_rating,
                  y0=0,
                  x1=avg_rating,
                  y1=max(prices) * 1.1,
                  line=dict(color="gray", width=1, dash="dash"))

    fig.add_shape(type="line",
                  x0=0,
                  y0=avg_price,
                  x1=5,
                  y1=avg_price,
                  line=dict(color="gray", width=1, dash="dash"))

    # Add quadrant labels
    fig.add_annotation(x=avg_rating + (5 - avg_rating) / 2,
                       y=avg_price + (max(prices) - avg_price) / 2,
                       text="Premium<br>(High Quality, High Price)",
                       showarrow=False,
                       font=dict(size=10))

    fig.add_annotation(x=avg_rating / 2,
                       y=avg_price + (max(prices) - avg_price) / 2,
                       text="Overpriced<br>(Low Quality, High Price)",
                       showarrow=False,
                       font=dict(size=10))

    fig.add_annotation(x=avg_rating + (5 - avg_rating) / 2,
                       y=avg_price / 2,
                       text="Value<br>(High Quality, Low Price)",
                       showarrow=False,
                       font=dict(size=10))

    fig.add_annotation(x=avg_rating / 2,
                       y=avg_price / 2,
                       text="Economy<br>(Low Quality, Low Price)",
                       showarrow=False,
                       font=dict(size=10))

    # Update layout
    fig.update_layout(title="Market Positioning Map: Price vs. Quality",
                      xaxis_title="Rating (1-5)",
                      yaxis_title="Price ($)",
                      template="plotly_white",
                      height=700,
                      width=900,
                      xaxis=dict(range=[0, 5.5],
                                 tickmode='linear',
                                 tick0=0,
                                 dtick=1),
                      margin=dict(l=50, r=50, t=80, b=50))

    return pio.to_json(fig)

def create_amenity_gap_analysis(hotel_name=None):
    """
    Creates a Plotly visualization for amenity gap analysis.
    Compares amenities of a selected hotel against competitors.
    
    Args:
        hotel_name (str, optional): The name of the hotel to analyze. If None, uses the first hotel in data.
    
    Returns:
        str: JSON representation of the Plotly figure
    """
    global scraped_data
    
    if not scraped_data:
        return "{}"  # Return empty JSON object
        
    # Extract amenities data
    hotels_with_amenities = []
    for hotel in scraped_data:
        if 'amenities' not in hotel or hotel['amenities'] == "N/A":
            continue
            
        # Parse amenities (assuming they're stored as comma-separated strings)
        amenities_list = [a.strip() for a in hotel['amenities'].split(',')]
        
        hotels_with_amenities.append({
            "name": hotel['name'],
            "amenities": amenities_list
        })
    
    if not hotels_with_amenities:
        return "{}"
    
    # If no hotel name is provided, use the first one
    if hotel_name is None or hotel_name not in [h['name'] for h in hotels_with_amenities]:
        hotel_name = hotels_with_amenities[0]['name']
    
    # Get the target hotel
    target_hotel = next((h for h in hotels_with_amenities if h['name'] == hotel_name), None)
    if not target_hotel:
        return "{}"
    
    # Find all unique amenities across all hotels
    all_amenities = set()
    for hotel in hotels_with_amenities:
        all_amenities.update(hotel['amenities'])
    
    # Count how many competitors have each amenity
    amenity_counts = {amenity: 0 for amenity in all_amenities}
    total_competitors = len(hotels_with_amenities) - 1  # Exclude the target hotel
    
    for hotel in hotels_with_amenities:
        if hotel['name'] == hotel_name:
            continue  # Skip the target hotel
        
        for amenity in hotel['amenities']:
            amenity_counts[amenity] += 1
    
    # Calculate percentage of competitors with each amenity
    amenity_percentages = {amenity: (count / total_competitors) * 100 for amenity, count in amenity_counts.items()}
    
    # Categorize amenities for the target hotel
    unique_amenities = []  # Amenities only the target hotel has
    common_amenities = []  # Amenities the target hotel shares with others
    missing_amenities = []  # Amenities competitors have but target hotel doesn't
    
    for amenity in all_amenities:
        has_amenity = amenity in target_hotel['amenities']
        percentage = amenity_percentages[amenity]
        
        if has_amenity and percentage == 0:
            unique_amenities.append(amenity)
        elif has_amenity:
            common_amenities.append((amenity, percentage))
        else:
            missing_amenities.append((amenity, percentage))
    
    # Sort amenities by percentage (descending)
    common_amenities.sort(key=lambda x: x[1], reverse=True)
    missing_amenities.sort(key=lambda x: x[1], reverse=True)
    
    # Prepare data for visualization
    fig = go.Figure()
    
    # Bar colors
    unique_color = 'rgb(39, 174, 96)'     # Green
    common_color = 'rgb(52, 152, 219)'    # Blue
    missing_color = 'rgb(231, 76, 60)'    # Red
    
    # Add unique amenities
    if unique_amenities:
        fig.add_trace(go.Bar(
            y=unique_amenities,
            x=[100] * len(unique_amenities),  # Set to 100% as these are unique
            orientation='h',
            name='Unique Amenities',
            marker=dict(color=unique_color),
            text=['Unique'] * len(unique_amenities),
            textposition='inside',
            hovertemplate='<b>%{y}</b><br>Unique to this hotel<extra></extra>'
        ))
    
    # Add common amenities
    if common_amenities:
        common_names = [item[0] for item in common_amenities]
        common_percentages = [item[1] for item in common_amenities]
        
        fig.add_trace(go.Bar(
            y=common_names,
            x=common_percentages,
            orientation='h',
            name='Common Amenities',
            marker=dict(color=common_color),
            text=[f"{p:.1f}%" for p in common_percentages],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>%{x:.1f}% of competitors have this<extra></extra>'
        ))
    
    # Add missing amenities
    if missing_amenities:
        missing_names = [item[0] for item in missing_amenities]
        missing_percentages = [item[1] for item in missing_amenities]
        
        fig.add_trace(go.Bar(
            y=missing_names,
            x=missing_percentages,
            orientation='h',
            name='Missing Amenities',
            marker=dict(color=missing_color),
            text=[f"{p:.1f}%" for p in missing_percentages],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>%{x:.1f}% of competitors have this<extra></extra>'
        ))
    
    # Update layout
    fig.update_layout(
        title=f"Amenity Gap Analysis for {hotel_name}",
        xaxis_title="Percentage of Competitors (%)",
        yaxis_title="Amenities",
        template="plotly_white",
        barmode='group',
        height=max(500, 100 + 25 * len(all_amenities)),  # Dynamic height based on number of amenities
        width=900,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=150, r=50, t=80, b=50)  # Increase left margin for amenity names
    )
    
    # Add annotations for recommendations
    recommendations = []
    
    # Add high-priority missing amenities (those that >50% of competitors have)
    high_priority = [item for item in missing_amenities if item[1] > 50]
    if high_priority:
        high_names = ", ".join([item[0] for item in high_priority[:3]])  # Top 3
        recommendations.append(f"Consider adding: {high_names}")
    
    # Add unique selling points
    if unique_amenities:
        unique_names = ", ".join(unique_amenities[:3])  # Top 3
        recommendations.append(f"Highlight unique features: {unique_names}")
    
    # Add the recommendations as annotations
    for i, rec in enumerate(recommendations):
        fig.add_annotation(
            x=0.5,
            y=-0.15 - (i * 0.05),
            xref="paper",
            yref="paper",
            text=rec,
            showarrow=False,
            font=dict(size=14),
            align="center",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.3)",
            borderwidth=1,
            borderpad=4
        )
    
    return pio.to_json(fig)

if __name__ == '__main__':
    app.run(debug=True)
