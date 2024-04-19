from flask import Flask,render_template,request
from flask import Flask, request, jsonify, render_template
from transformers import T5ForConditionalGeneration, T5Tokenizer
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi as ytt

import pandas as pd
import numpy as np
import pickle
import sqlite3
import random

import smtplib 
from email.message import EmailMessage
from datetime import datetime


# define a variable to hold you app
app = Flask(__name__)

# initialize the model architecture and weights
model = T5ForConditionalGeneration.from_pretrained("t5-small")
# initialize the model tokenizer
tokenizer = T5Tokenizer.from_pretrained("t5-small")
# define your resource endpoints

@app.route('/')
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/index')
def index():
    return render_template('index.html')


#extracts id from url
def extract_video_id(url:str):
    
    query = urlparse(url)
    if query.hostname == 'youtu.be': return query.path[1:]
    if query.hostname in {'www.youtube.com', 'youtube.com'}:
        if query.path == '/watch': return parse_qs(query.query)['v'][0]
        if query.path[:7] == '/embed/': return query.path.split('/')[2]
        if query.path[:3] == '/v/': return query.path.split('/')[2]
    # fail?
    return None

def summarizer(script):
    # encode the text into tensor of integers using the appropriate tokenizer
    input_ids = tokenizer("summarize: " + script, return_tensors="pt", max_length=512, truncation=True).input_ids
    # generate the summarization output
    outputs = model.generate(
        input_ids, 
        max_length=150, 
        min_length=40, 
        length_penalty=2.0, 
        num_beams=4, 
        early_stopping=True)

    summary_text = tokenizer.decode(outputs[0])
    return(summary_text)


@app.route('/summarize',methods=['GET','POST'])
def video_transcript():
    if request.method == 'POST':
        url = request.form['youtube_url']
        video_id = extract_video_id(url)
        data = ytt.get_transcript(video_id,languages=['de', 'en'])
        
        scripts = []
        for text in data:
            for key,value in text.items():
                if(key=='text'):
                    scripts.append(value)
        transcript = " ".join(scripts)
        summary = summarizer(transcript)
        #print(summary)
        return render_template('result.html', output = summary, youtubeurl = url)
    else:
        return render_template('result.html', output = "ERROR")

@app.route('/logon')
def logon():
	return render_template('signup.html')

@app.route('/login')
def login():
	return render_template('signin.html')


@app.route("/signup")
def signup():
    global otp, username, name, email, number, password
    username = request.args.get('user','')
    name = request.args.get('name','')
    email = request.args.get('email','')
    number = request.args.get('mobile','')
    password = request.args.get('password','')
    otp = random.randint(1000,5000)
    print(otp)
    msg = EmailMessage()
    msg.set_content("Your OTP is : "+str(otp))
    msg['Subject'] = 'OTP'
    msg['From'] = "evotingotp4@gmail.com"
    msg['To'] = email
    
    
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("evotingotp4@gmail.com", "xowpojqyiygprhgr")
    s.send_message(msg)
    s.quit()
    return render_template("val.html")

@app.route('/predict_lo', methods=['POST'])
def predict_lo():
    global otp, username, name, email, number, password
    if request.method == 'POST':
        message = request.form['message']
        print(message)
        if int(message) == otp:
            print("TRUE")
            con = sqlite3.connect('signup.db')
            cur = con.cursor()
            cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",(username,email,password,number,name))
            con.commit()
            con.close()
            return render_template("signin.html")
    return render_template("signup.html")

@app.route("/signin")
def signin():

    mail1 = request.args.get('user','')
    password1 = request.args.get('password','')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?",(mail1,password1,))
    data = cur.fetchone()

    if data == None:
        return render_template("signin.html")    

    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("index.html")
    else:
        return render_template("signin.html")


@app.route("/notebook")
def notebook():
    return render_template("Notebook.html")


    
# server the app when this file is run
if __name__ == '__main__':
    app.run()