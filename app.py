import time
import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template
import pandas as pd
import os
from flask import jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import matplotlib.pyplot as plt

# Set up credentials and access Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name('watchtime-400918-f2c45c63501c.json', scope)
client = gspread.authorize(creds)

sheet = client.open("kranti Data - Lectures").sheet1
df = pd.DataFrame(sheet.get_all_records())

app = Flask(__name__)
app.config['STATIC_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')

@app.route('/')
def index():
    return render_template('index.html')

def plot_course_wise_data(course_name):
    course_data = df[df['CourseName'] == course_name].reset_index()
    avg_duration = course_data['Minute'].mean()

    plt.figure(figsize=(10, 6))
    plt.bar(course_data['Videoname'], course_data['Minute'])
    plt.xlabel('Video Name')
    plt.ylabel('Minutes')
    plt.title(f'Minutes by Video for Course: {course_name}')
    plt.xticks(rotation=90)
    plt.tight_layout()

    plot_file_name = 'plot_course.png'
    plot_path = os.path.join(app.config['STATIC_FOLDER'], image_filename)
    plt.savefig(plot_file)
    plt.close()

    return plot_file_name, avg_duration

def plot_video_wise_data(video_name):
    timestamp = int(time.time())
    # Filter rows that match the given video name
    video_data = df[df['VideoName'] == video_name]
    
    # Group by 'CourseName' and sum 'WatchTime(Mins)'
    minutes_by_course = video_data.groupby('CourseName')['WatchTime(Mins)'].sum()
    
    # Calculate the total minutes across all courses
    total_minutes = minutes_by_course.sum()

    # Plotting
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plotting individual watch times as bars
    ax1.bar(minutes_by_course.index, minutes_by_course, color='b', alpha=0.6)
    ax1.set_xlabel('Course Name')
    ax1.set_ylabel('Minutes', color='b')
    ax1.tick_params('y', colors='b')
    ax1.set_title(f'Minutes by Course for Video: {video_name}')
    ax1.set_xticklabels(minutes_by_course.index, rotation=90)
    ax1.set_ylim([0, total_minutes + 10])  # Set the y-axis limit a bit more than the total_minutes for clear visualization
    
    # Adding total watch time as a horizontal line
    ax2 = ax1.twinx()
    ax2.hlines(total_minutes, xmin=-0.5, xmax=len(minutes_by_course)-0.5, color='r', linestyle='--')
    ax2.set_ylabel('Total Minutes', color='r')
    ax2.tick_params('y', colors='r')
    ax2.set_ylim([0, total_minutes + 10])  # Ensure the y-axis limits match

    plt.tight_layout()

    # Save the plot and return its file name
    image_filename = f"plot_video_{timestamp}.png"
    plot_path = os.path.join("static", image_filename)
    plt.savefig(plot_path)
    plt.close()

    return image_filename, total_minutes, minutes_by_course.to_dict()


@app.route('/plot/course/<course_name>')
def plot_course(course_name):
    plot_file_name, avg_duration = plot_course_wise_data(course_name)
    return render_template('course_plot.html', plot_file=plot_file_name, avg_duration=avg_duration, course_name=course_name)

@app.route('/plot/video/<video_name>')
def plot_video(video_name):
    plot_file, total_minutes, course_watchtimes = plot_video_wise_data(video_name)
    timestamp = int(time.time())  # Get the current timestamp
    return render_template('video_plots.html', plot_file=plot_file, total_minutes=total_minutes, video_name=video_name, course_watchtimes=course_watchtimes, timestamp=timestamp)

@app.route('/get_courses')
def get_courses():
    courses = df['CourseName'].unique().tolist()
    return jsonify(courses)

@app.route('/get_videos/<course_name>')
def get_videos(course_name):
    videos = df[df['CourseName'] == course_name]['VideoName'].unique().tolist()
    return jsonify(videos)


if __name__ == "__main__":
    app.run(debug=True)
