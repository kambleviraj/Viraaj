import pandas as pd
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os

# Initialize the Flask application
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# --- Data Loading ---
def load_data(college_type):
    """
    Loads and preprocesses data from the appropriate CSV file.
    :param college_type: 'junior' or 'engineering'
    """
    if college_type == 'junior':
        filepath = 'junior_colleges.csv'
        cutoff_col = 'cutoff_10th'
    elif college_type == 'engineering':
        filepath = 'engineering_colleges.csv'
        cutoff_col = 'cutoff_cet'
    else:
        return None # Return None if the type is invalid

    if not os.path.exists(filepath):
        return pd.DataFrame() # Return empty dataframe if file doesn't exist

    df = pd.read_csv(filepath)

    # --- Data Cleaning ---
    df[cutoff_col] = pd.to_numeric(df[cutoff_col], errors='coerce')
    df.fillna({cutoff_col: 0}, inplace=True)
    df['category'] = df['category'].astype(str).str.upper()

    return df

# --- Flask Routes ---
@app.route('/')
def index():
    """Renders the main HTML page."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """
    Handles the prediction logic based on the type of college.
    """
    try:
        data = request.get_json()
        college_type = data['college_type']
        student_marks = float(data['marks'])
        student_category = data['category'].upper()
    except (ValueError, KeyError):
        return jsonify({'error': 'Invalid input. Please check your entries.'}), 400

    colleges_df = load_data(college_type)
    if colleges_df is None or colleges_df.empty:
        return jsonify({'error': f'Could not load data for {college_type} colleges.'}), 500
        
    # Determine the correct cutoff column based on the college type
    cutoff_col = 'cutoff_10th' if college_type == 'junior' else 'cutoff_cet'

    # --- Filtering Logic ---
    # Find colleges that match the student's category and where the student's marks
    # are greater than or equal to the college's cutoff marks.
    eligible_colleges = colleges_df[
        (colleges_df['category'] == student_category) &
        (student_marks >= colleges_df[cutoff_col])
    ].copy()

    # Sort results and SAVE the sorted copy
    sorted_colleges = eligible_colleges.sort_values(by=cutoff_col, ascending=False)

    # Rename the column on the sorted copy and SAVE the result
    renamed_colleges = sorted_colleges.rename(columns={cutoff_col: 'cutoff'})

    # Convert the final, modified data to a dictionary
    results = renamed_colleges.to_dict('records')

    return jsonify(results)

# --- Main Execution ---
if __name__ == '__main__':
    # Runs the Flask app on localhost with debugging enabled.
    app.run(debug=True)
  