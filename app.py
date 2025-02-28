from PyPDF2 import PdfReader
from flask import Flask, request, render_template, session, redirect, url_for
import docx
import re
import os

app = Flask(__name__)
app.secret_key = "aiproject1"

directory_path = "CV" 
if not os.path.exists(directory_path):
    os.makedirs(directory_path) 

cv_files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]

def extention(ch):
    if ch == "":
        return -1
    elif ch[0] == ".":
        return ch[0:]
    else:
        return extention(ch[1:])

def extract_text_from_file(fn):
    ext = extention(fn)
    text = ""

    if ext == ".pdf":
        with open(os.path.join(directory_path, fn), "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    elif ext == ".docx":
        doc = docx.Document(os.path.join(directory_path, fn))
        for para in doc.paragraphs:
            text += para.text
        return text
    else:
        print("Unsupported file format")
        return ""

def extract_data_from_cvs(files,job_descriptions,skills):
    #skills = ['Python', 'Machine Learning', 'Data Science', 'Computer Science', 'SQL']
    #job_descriptions = [
    #    "Software Engineer",
    #    #"Data Scientist",
    #    "Data Analyst"
    #]
    data = []
    for file in files:
        text = extract_text_from_file(file)
        if text:
            founded_skills, experiences = extr_info(text, skills, job_descriptions)
            score = calculate_cv_score(len(founded_skills) + len(experiences), len(skills) + len(job_descriptions))
            data.append([file, score])
    return data

def extr_info(donne, skills, job_descriptions):
    found_skills = []
    found_exp = []

    for skill in skills:
        if re.search(skill, donne, re.IGNORECASE):
            found_skills.append(skill)

    for exp in job_descriptions:
        if re.search(exp, donne, re.IGNORECASE):
            found_exp.append(exp)

    return found_skills, found_exp

def calculate_cv_score(matches, somme):
    return f"{(matches * 100) / somme:.2f}" if somme != 0 else "0.00"

def rank_cvs(data):
    data.sort(key=lambda x: float(x[1]), reverse=True)
    return data


@app.route("/", methods=["GET", "POST"])
def index():
    global directory_path, cv_files
    
    if "directory_path" not in session:
        session["directory_path"] = directory_path
    if "job_descriptions" not in session:
        session["job_descriptions"] = []
    if "skills" not in session:
        session["skills"] = []
    
    ranked_cvs = []

    if request.method == "POST":
        session["directory_path"] = request.form['directory']
        directory_path = session["directory_path"]
        cv_files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        
        new_job_desc = request.form.get('job_desc', '').strip()
        new_skill = request.form.get('skills', '').strip()

        if new_job_desc:
            session["job_descriptions"].append(new_job_desc)
        if new_skill:
            session["skills"].append(new_skill)

        session.modified = True
        
        extracted_data = extract_data_from_cvs(cv_files,session["job_descriptions"],session["skills"])
        ranked_cvs = rank_cvs(extracted_data)

    return render_template("index.html", cvs_ranked=ranked_cvs, job_descr=session["job_descriptions"],skill=session["skills"], directory_path=session["directory_path"])

@app.route("/clear", methods=["POST"])
def clear_session():
    session["directory_path"] = "CV"
    session["job_descriptions"] = []
    session["skills"] = []
    session.modified = True
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5015)