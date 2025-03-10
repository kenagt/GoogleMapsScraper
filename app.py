import os
import threading
import pandas as pd
from flask import Flask, render_template, redirect, url_for, flash, request
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

    # Get amenity analysis and hotel names
    amenity_analysis_json, hotels_with_amenities = create_amenity_gap_analysis(
    )

    return render_template('index.html',
                           data=data,
                           scraping_in_progress=scraping_in_progress,
                           rating_distribution_json=rating_distribution_json,
                           price_distribution_json=price_distribution_json,
                           market_positioning_json=market_positioning_json,
                           amenity_analysis_json=amenity_analysis_json,
                           hotels_with_amenities=hotels_with_amenities)


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
                "name": name.replace("'", ""),
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
        tuple: (str: JSON representation of the Plotly figure, list: hotel names with amenities)
    """
    global scraped_data

    if not scraped_data:
        return "{}", []  # Return empty JSON object and empty list

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
        return "{}", []

    # Get list of hotel names for dropdown
    hotel_names = [h['name'] for h in hotels_with_amenities]

    # If no hotel name is provided, use the first one
    if hotel_name is None or hotel_name not in hotel_names:
        hotel_name = hotel_names[0] if hotel_names else None

    # Exit early if we have no valid hotels
    if not hotel_name:
        return "{}", hotel_names

    # Get the target hotel
    target_hotel = next(
        (h for h in hotels_with_amenities if h['name'] == hotel_name), None)
    if not target_hotel:
        return "{}", hotel_names

    # Find all unique amenities across all hotels
    all_amenities = set()
    for hotel in hotels_with_amenities:
        all_amenities.update(hotel['amenities'])

    # Count how many competitors have each amenity
    amenity_counts = {amenity: 0 for amenity in all_amenities}
    total_competitors = len(
        hotels_with_amenities) - 1  # Exclude the target hotel

    for hotel in hotels_with_amenities:
        if hotel['name'] == hotel_name:
            continue  # Skip the target hotel

        for amenity in hotel['amenities']:
            amenity_counts[amenity] += 1

    # Calculate percentage of competitors with each amenity
    amenity_percentages = {
        amenity:
        (count / total_competitors) * 100 if total_competitors > 0 else 0
        for amenity, count in amenity_counts.items()
    }

    # Categorize amenities for the target hotel
    unique_amenities = []  # Amenities only the target hotel has
    common_amenities = []  # Amenities the target hotel shares with others
    missing_amenities = [
    ]  # Amenities competitors have but target hotel doesn't

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
    unique_color = 'rgb(39, 174, 96)'  # Green
    common_color = 'rgb(52, 152, 219)'  # Blue
    missing_color = 'rgb(231, 76, 60)'  # Red

    # Add unique amenities
    if unique_amenities:
        fig.add_trace(
            go.Bar(
                y=unique_amenities,
                x=[100] *
                len(unique_amenities),  # Set to 100% as these are unique
                orientation='h',
                name='Unique Amenities',
                marker=dict(color=unique_color),
                text=['Unique'] * len(unique_amenities),
                textposition='inside',
                hovertemplate=
                '<b>%{y}</b><br>Unique to this hotel<extra></extra>'))

    # Add common amenities
    if common_amenities:
        common_names = [item[0] for item in common_amenities]
        common_percentages = [item[1] for item in common_amenities]

        fig.add_trace(
            go.Bar(
                y=common_names,
                x=common_percentages,
                orientation='h',
                name='Common Amenities',
                marker=dict(color=common_color),
                text=[f"{p:.1f}%" for p in common_percentages],
                textposition='outside',
                hovertemplate=
                '<b>%{y}</b><br>%{x:.1f}% of competitors have this<extra></extra>'
            ))

    # Add missing amenities
    if missing_amenities:
        missing_names = [item[0] for item in missing_amenities]
        missing_percentages = [item[1] for item in missing_amenities]

        fig.add_trace(
            go.Bar(
                y=missing_names,
                x=missing_percentages,
                orientation='h',
                name='Missing Amenities',
                marker=dict(color=missing_color),
                text=[f"{p:.1f}%" for p in missing_percentages],
                textposition='outside',
                hovertemplate=
                '<b>%{y}</b><br>%{x:.1f}% of competitors have this<extra></extra>'
            ))

    # Update layout
    fig.update_layout(
        title=f"Amenity Gap Analysis for {hotel_name}",
        xaxis_title="Percentage of Competitors (%)",
        yaxis_title="Amenities",
        template="plotly_white",
        barmode='group',
        height=max(
            500, 100 + 25 *
            len(all_amenities)),  # Dynamic height based on number of amenities
        width=900,
        legend=dict(orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1),
        margin=dict(l=150, r=50, t=80,
                    b=50)  # Increase left margin for amenity names
    )

    # Add annotations for recommendations
    recommendations = []

    # Add high-priority missing amenities (those that >50% of competitors have)
    high_priority = [item for item in missing_amenities if item[1] > 50]
    if high_priority:
        high_names = ", ".join([item[0]
                                for item in high_priority[:3]])  # Top 3
        recommendations.append(f"Consider adding: {high_names}")

    # Add unique selling points
    if unique_amenities:
        unique_names = ", ".join(unique_amenities[:3])  # Top 3
        recommendations.append(f"Highlight unique features: {unique_names}")

    # Add the recommendations as annotations
    for i, rec in enumerate(recommendations):
        fig.add_annotation(x=0.5,
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
                           borderpad=4)

    return pio.to_json(fig), hotel_names


def create_bar_comparison(hotel_data):
    """
    Create a bar chart comparing key metrics across selected hotels.
    """
    # Define metrics to compare
    metrics = {
        'averageReviewScore': 'Average Rating',
        'averageOtaPrice': 'Average Price ($)',
        'numberOfReviews': 'Number of Reviews',
    }

    # Extract hotel names
    hotel_names = [hotel['name'] for hotel in hotel_data]

    # Create figure with subplots
    fig = go.Figure()

    # Add a trace for each metric
    for metric_key, metric_name in metrics.items():
        metric_values = []

        for hotel in hotel_data:
            value = hotel.get(metric_key, 'N/A')

            # Handle N/A values
            if value == 'N/A':
                metric_values.append(0)
                continue

            # Convert to float and handle different formats
            try:
                if isinstance(value, str):
                    value = value.replace(',', '.')
                metric_values.append(float(value))
            except (ValueError, TypeError):
                metric_values.append(0)

        # Add bar for this metric
        fig.add_trace(
            go.Bar(
                x=hotel_names,
                y=metric_values,
                name=metric_name,
                text=[f"{v:.1f}" if v > 0 else 'N/A' for v in metric_values],
                textposition='auto'))

    # Update layout
    fig.update_layout(title="Hotel Key Metrics Comparison",
                      xaxis_title="Hotels",
                      yaxis_title="Values",
                      barmode='group',
                      template="plotly_white",
                      height=500,
                      legend=dict(orientation="h",
                                  yanchor="bottom",
                                  y=1.02,
                                  xanchor="right",
                                  x=1))

    return pio.to_json(fig)


def create_radar_comparison(hotel_data):
    """
    Create a radar chart comparing multiple metrics across selected hotels.
    """
    # Define metrics to include in radar chart
    metrics = {
        'averageReviewScore': 'Rating',
        'numberOfReviews': 'Review Count',
        'averageOtaPrice': 'Price',
    }

    # Add amenities count if available
    for hotel in hotel_data:
        if 'amenities' in hotel and hotel['amenities'] != 'N/A':
            # Count amenities
            amenities = hotel['amenities'].split(',')
            hotel['amenities_count'] = len(amenities)
        else:
            hotel['amenities_count'] = 0

    metrics['amenities_count'] = 'Amenities Count'

    # Normalize all metrics to a 0-10 scale
    normalized_data = []

    # First pass: get min/max for each metric
    metric_ranges = {}
    for metric in metrics.keys():
        values = []
        for hotel in hotel_data:
            value = hotel.get(metric, 'N/A')
            if value != 'N/A':
                try:
                    if isinstance(value, str):
                        value = value.replace(',', '.')
                    values.append(float(value))
                except (ValueError, TypeError):
                    pass

        if values:
            metric_ranges[metric] = {'min': min(values), 'max': max(values)}
        else:
            metric_ranges[metric] = {
                'min': 0,
                'max': 1
            }  # Avoid division by zero

    # Second pass: normalize the data
    for hotel in hotel_data:
        hotel_normalized = {'name': hotel['name']}

        for metric, display_name in metrics.items():
            value = hotel.get(metric, 'N/A')

            if value == 'N/A':
                hotel_normalized[metric] = 0
                continue

            try:
                if isinstance(value, str):
                    value = value.replace(',', '.')
                value = float(value)

                # Special handling for price (inverse normalization - lower is better)
                if metric == 'averageOtaPrice':
                    min_val = metric_ranges[metric]['min']
                    max_val = metric_ranges[metric]['max']
                    if max_val == min_val:
                        normalized = 5  # If all same price, give middle value
                    else:
                        normalized = 10 - (((value - min_val) /
                                            (max_val - min_val)) * 10)
                else:
                    # Normal normalization (higher is better)
                    min_val = metric_ranges[metric]['min']
                    max_val = metric_ranges[metric]['max']
                    if max_val == min_val:
                        normalized = 5  # If all values same, give middle value
                    else:
                        normalized = ((value - min_val) /
                                      (max_val - min_val)) * 10

                hotel_normalized[metric] = normalized
            except (ValueError, TypeError):
                hotel_normalized[metric] = 0

        normalized_data.append(hotel_normalized)

    # Create the radar chart
    fig = go.Figure()

    # Prepare the categories (theta axis)
    categories = list(metrics.values())

    # Add a trace for each hotel
    for hotel in normalized_data:
        values = [hotel[metric] for metric in metrics.keys()]
        # Add the first value again to close the loop
        values.append(values[0])
        categories_closed = categories + [categories[0]]

        fig.add_trace(
            go.Scatterpolar(r=values,
                            theta=categories_closed,
                            fill='toself',
                            name=hotel['name']))

    # Update layout
    fig.update_layout(title="Hotel Performance Radar Chart",
                      polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                      template="plotly_white",
                      height=500,
                      width=700,
                      showlegend=True)

    return pio.to_json(fig)


def create_amenities_comparison(hotel_data):
    """
    Create a comparison of amenities across selected hotels.
    """
    # Extract amenities for each hotel
    hotel_amenities = {}
    all_amenities = set()

    for hotel in hotel_data:
        name = hotel['name']
        if 'amenities' in hotel and hotel['amenities'] != 'N/A':
            amenities_list = [a.strip() for a in hotel['amenities'].split(',')]
            hotel_amenities[name] = amenities_list
            all_amenities.update(amenities_list)
        else:
            hotel_amenities[name] = []

    # Convert to sorted list
    all_amenities = sorted(list(all_amenities))

    # Create heatmap data
    hotels = list(hotel_amenities.keys())
    z_data = []

    for amenity in all_amenities:
        row = []
        for hotel in hotels:
            if amenity in hotel_amenities[hotel]:
                row.append(1)  # Hotel has this amenity
            else:
                row.append(0)  # Hotel doesn't have this amenity
        z_data.append(row)

    # Create the heatmap
    fig = go.Figure(
        data=go.Heatmap(z=z_data,
                        x=hotels,
                        y=all_amenities,
                        colorscale=[[0, 'indianred'], [1, 'green']],
                        showscale=False))

    # Add annotations
    annotations = []
    for i, amenity in enumerate(all_amenities):
        for j, hotel in enumerate(hotels):
            if amenity in hotel_amenities[hotel]:
                annotations.append(
                    dict(x=hotel,
                         y=amenity,
                         text="✓",
                         showarrow=False,
                         font=dict(color="black")))

    # Update layout
    fig.update_layout(title="Hotel Amenities Comparison",
                      height=max(500, 100 + 25 * len(all_amenities)),
                      width=900,
                      template="plotly_white",
                      annotations=annotations,
                      xaxis=dict(title="Hotels"),
                      yaxis=dict(title="Amenities"))

    return pio.to_json(fig)


def create_value_comparison(hotel_data):
    """
    Create a value for money comparison (rating vs price)
    """
    hotels = []

    for hotel in hotel_data:
        name = hotel['name']
        rating = hotel.get('averageReviewScore', 'N/A')
        price = hotel.get('averageOtaPrice', 'N/A')

        # Skip hotels with missing data
        if rating == 'N/A' or price == 'N/A':
            continue

        try:
            if isinstance(rating, str):
                rating = rating.replace(',', '.')
            if isinstance(price, str):
                price = price.replace(',', '.')

            rating = float(rating)
            price = float(price)

            # Calculate value score (rating/price ratio)
            value_score = (rating / price) * 100

            hotels.append({
                'name': name,
                'rating': rating,
                'price': price,
                'value_score': value_score
            })
        except (ValueError, TypeError, ZeroDivisionError):
            continue

    if not hotels:
        return json.dumps({"error": "No valid data for comparison"})

    # Sort by value score (descending)
    hotels.sort(key=lambda x: x['value_score'], reverse=True)

    # Create the chart
    fig = go.Figure()

    # Add bar chart for value scores
    fig.add_trace(
        go.Bar(x=[h['name'] for h in hotels],
               y=[h['value_score'] for h in hotels],
               marker_color='blue',
               name='Value Score',
               text=[
                   f"{score:.2f}"
                   for score in [h['value_score'] for h in hotels]
               ],
               textposition='auto'))

    # Add line chart for ratings
    fig.add_trace(
        go.Scatter(x=[h['name'] for h in hotels],
                   y=[h['rating'] for h in hotels],
                   mode='lines+markers',
                   name='Rating',
                   yaxis='y2',
                   line=dict(color='green', width=3),
                   marker=dict(size=10)))

    # Update layout with dual y-axes
    fig.update_layout(title="Hotel Value for Money Analysis",
                      xaxis=dict(title="Hotels"),
                      yaxis=dict(title="Value Score (Rating/Price × 100)",
                                 side="left",
                                 color="blue"),
                      yaxis2=dict(title="Rating",
                                  side="right",
                                  overlaying="y",
                                  range=[0, 5],
                                  color="green"),
                      template="plotly_white",
                      height=500,
                      width=900,
                      legend=dict(orientation="h",
                                  yanchor="bottom",
                                  y=1.02,
                                  xanchor="right",
                                  x=1))

    return pio.to_json(fig)


@app.route('/amenity_analysis')
def amenity_analysis():
    hotel_name = request.args.get('hotel_name', None)
    analysis_json, _ = create_amenity_gap_analysis(hotel_name)
    return analysis_json


@app.route('/hotel_comparison')
def hotel_comparison():
    """
    Generate comparison data for selected hotels based on the comparison type.
    """
    global scraped_data

    # Get request parameters
    hotels_json = request.args.get('hotels', '[]')
    comparison_type = request.args.get('comparison_type', 'bar')

    try:
        selected_hotels = json.loads(hotels_json)

        # Validate input
        if not selected_hotels or len(selected_hotels) < 2:
            return json.dumps({"error": "Please select at least 2 hotels"})

        # Get data for selected hotels
        hotel_data = []
        for hotel in scraped_data:
            if hotel['name'] in selected_hotels:
                hotel_data.append(hotel)

        # Generate the appropriate chart based on comparison type
        if comparison_type == 'bar':
            return create_bar_comparison(hotel_data)
        elif comparison_type == 'radar':
            return create_radar_comparison(hotel_data)
        elif comparison_type == 'amenities':
            return create_amenities_comparison(hotel_data)
        elif comparison_type == 'value':
            return create_value_comparison(hotel_data)
        else:
            return json.dumps({"error": "Invalid comparison type"})

    except Exception as e:
        app.logger.error(f"Comparison error: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})


if __name__ == '__main__':
    app.run(debug=True)
