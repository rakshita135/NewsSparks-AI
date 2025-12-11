import requests
import json
import streamlit as st
from google import genai
from datetime import datetime
import time
from google.genai.errors import ServerError
# from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer # type: ignore
from reportlab.lib.styles import getSampleStyleSheet # type: ignore
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.lib.units import inch # type: ignore
from io import BytesIO

client=genai.Client(api_key=GEMINI_API_KEY)
model_name="models/gemini-flash-latest"

def fetch_news():
    url="https://newsdata.io/api/1/latest?apikey=pub_77f90df199c74cc18bd1397aac8e3696&country=in&language=hi,en,gu&category=breaking,education,science,sports,technology"
    response=requests.get(url)

    if response.status_code != 200:
        return []
    
    data=response.json()
    # print(data)
    articles=data.get("results",[])
    return articles

# def summarize_with_gemini(text):
    # prompt=f"Summarize the following news {text} using this instructions:\n{context}"
    # response=client.models.generate_content(
    #     model=model_name,
    #     contents=prompt)
    # return response.text
    import time


def summarize_with_gemini(text, retries=5):
    prompt = f"Summarize the following news :{text} in {language} by following this instruction:\n{context}"

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        
        except ServerError as e:
            if "overloaded" in str(e).lower() or "503" in str(e):
                wait = 2 ** attempt   # exponential backoff
                st.warning(f"Gemini is overloaded. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise e
    
    return "⚠ Gemini overloaded. Try again later."


def generate_pdf(summary_list):
    buffer = BytesIO()
    doc=SimpleDocTemplate(buffer,pagesize=letter,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40)
    styles=getSampleStyleSheet()
    title_style=styles["Heading2"]
    text_style=styles["BodyText"]
    story=[]
    story.append(Paragraph("AI News Summaries",styles["Title"]))
    story.append(Spacer(1,0.2*inch))

    for idx,item in enumerate(summary_list,start=1):
        title=item['title']
        summary=item['summary'].replace('\n','<br/>')
        story.append(Paragraph(f"<b>Title {idx} :</b>{title}",title_style))
        story.append(Spacer(1,0.1*inch))
        story.append(Paragraph(summary,text_style))
        story.append(Spacer(1,0.3*inch))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

   

st.set_page_config(page_title="AI News Summarizer")
st.title("AI News Summarizer")
st.write("Get News Summarised according to your Context")
lang_list=['English','Hindi', 'Bengali', 'Gujarati', 'Kannada', 'Malayalam', 'Marathi', 'Tamil', 'Telugu','Urdu']
language=st.selectbox("Enter your Preffered Language for summary:",
                      lang_list,
                      index=0,
                      placeholder="Select a language")
context=st.text_input("Enter you interest")

if st.button("Fetch and Summarize News"):
    st.info("Fetching news...")
    articles=fetch_news()

    if(len(articles)==0):
        st.error("Failed to fetch news")
    else:
        summarized_list=[]
        st.success(f"Fetched {len(articles)} articles!")
        st.divider()
    for i,article in enumerate(articles[:5],start=1):
        title=article.get('title','No title')
        desc=article.get('Description','')

        summary=summarize_with_gemini(desc if desc else title)
        st.subheader(f"{i}. {title}")
        st.write(summary)
        summarized_list.append({
        "title": title,
        "summary": summary
        })
        # st.markdown(summary)

# Generate PDF
    if(language=='English'):
        pdf_buffer = generate_pdf(summarized_list)

        st.download_button(
        label="Download Summary as PDF",
        data=pdf_buffer,
            file_name="news_summary.pdf",
        mime="application/pdf"
)

















