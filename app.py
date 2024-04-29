from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Define the upload folder

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare_sheets', methods=['POST'])
def compare_sheets():
    try:
        # Get the uploaded files from the request
        enroll_file = request.files['enroll_sheet']
        attendance_file = request.files['attendance_sheet']

        # Save the files to a temporary location
        enroll_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_enrollment.xlsx")
        attendance_path = os.path.join(app.config['UPLOAD_FOLDER'], "temp_attendance.csv")
        enroll_file.save(enroll_path)
        attendance_file.save(attendance_path)

        # Read data from uploaded files into DataFrames
        enroll_std = pd.read_excel(enroll_path, skiprows=9)
        attended_std = pd.read_csv(attendance_path, encoding='utf-16', delimiter='\t', skiprows=[1])

        # Rename the column in enroll_std to match the column name in attended_std
        enroll_std.rename(columns={'Name of the Student ': 'Name of the Student'}, inplace=True)

        # Merge DataFrames based on student names
        merged_df = pd.merge(enroll_std, attended_std, how='left', left_on='Name of the Student', right_on='Full Name')

        # Create a new DataFrame with columns for student name, roll number, and attendance status
        attendance_df = merged_df[['Name of the Student', 'Roll No.']]
        attendance_df['Appearance'] = 0

        # Iterate through attendance records and update the attendance status
        for index, row in attended_std.iterrows():
            name = row['Full Name']
            if name in merged_df['Name of the Student'].tolist():
                attendance_df.loc[attendance_df['Name of the Student'] == name, 'Appearance'] = 1

        # Save DataFrame to a new Excel file
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], "attendance_comparison.xlsx")
        attendance_df.to_excel(output_path, index=False)

        # Return response to client
        if os.path.exists(output_path):
            return jsonify({"success": True, "download_link": "/download/" + os.path.basename(output_path)})
        else:
            return jsonify({"success": False, "message": "Comparison failed."})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/download/<filename>')
def download(filename):
    directory = app.config['UPLOAD_FOLDER']
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
