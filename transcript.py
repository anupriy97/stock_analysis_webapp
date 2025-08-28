import os
import re
import pandas as pd
from PyPDF2 import PdfReader

from google_genai import fetch_response


def get_transcript_path(ticker: str, quarter: str) -> str:
    ticker_mapping = {
        "HDFCBANK.NS": "hdfc",
        "TITAN.NS": "titan"
    }
    filepath = f"./pdfs/{ticker_mapping[ticker]}_{quarter}.pdf"
    return filepath


def load_transcript(filepath: str) -> PdfReader:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f'File Path {filepath} not found.')
    reader = PdfReader(filepath)
    return reader


def preprocess_transcript(reader: PdfReader) -> pd.DataFrame:
    pages = reader.pages
    transcript_text_list = []

    transcript_begin_page_text = pages[2].extract_text()
    anchor_index = re.search('Moderator', transcript_begin_page_text).start()
    common_page_prefix = transcript_begin_page_text[:anchor_index].rstrip()
    common_page_prefix_pattern = re.sub("Page [0-9]+ of [0-9]+", "Page [0-9]+ of [0-9]+", common_page_prefix)
    
    for page in pages[2:]:
        text = page.extract_text()
        # text = r'\n \n'.join(text.split('\n \n')[1:])
        # text = text.replace(common_page_prefix, '')
        text = re.sub(common_page_prefix_pattern, '', text).lstrip()
        # print(text)
        transcript_text_list.append(text)
    
    transcript_text = '\n' + ' \n'.join(transcript_text_list)

    transcript_text = re.sub('([0-9]) ?:', r'\1*colon*', transcript_text)
    colon_splitted_list = transcript_text.split(':')
    colon_splitted_list = [re.sub('\*colon\*', ':', t) for t in colon_splitted_list]

    colon_newline_splitted_list = [
        # ['\n'.join(t.split('\n')[:-1]), t.split('\n')[-1]] if idx < (len(colon_splitted_list) - 1)  else [t]
        [''.join(re.split('(\? |\. |\n)', t)[:-1]), re.split('(\? |\. |\n)', t)[-1]] if idx < (len(colon_splitted_list) - 1)  else [t]
        for idx, t in enumerate(colon_splitted_list)
    ]
    colon_newline_splitted_list = [t for tlist in colon_newline_splitted_list for t in tlist][1:]
    speaker_list = colon_newline_splitted_list[::2]
    transcription_list = colon_newline_splitted_list[1::2]
    transcript_df = pd.DataFrame(data={
        'transcript_index': list(range(1, len(speaker_list) + 1)),
        'speaker': speaker_list,
        'transcript': transcription_list
    })

    management_text = pages[1].extract_text()

    transcript_df['speaker_type'] = transcript_df['speaker'].apply(lambda x: 'Management' if x.lower().replace(' ', '') in management_text.lower().replace(' ', '') else 'Question')
    transcript_df.loc[transcript_df['speaker'].apply(lambda x: 'Moderator' in x), 'speaker'] = 'Moderator'
    transcript_df.loc[transcript_df['speaker'].apply(lambda x: 'Moderator' in x), 'speaker_type'] = 'Moderator'
    return transcript_df


def extract_summary(transcript_df: pd.DataFrame) -> str:
    # Filter the text discussed by management and extract the highlights, if any
    first_question_tid = transcript_df[transcript_df['speaker_type'] == 'Question']['transcript_index'].min()
    management_df = transcript_df[transcript_df['transcript_index'] < first_question_tid]
    management_df = management_df[management_df['speaker_type'] == 'Management']
    management_text = '\n'.join(transcript_df['transcript'].values.tolist())
    management_context = f"This is the text from earnings transcript as told by management.\n\n{management_text}"

    # Filter the text discussed witihn Q&A and extract the highlights, if any
    qna_df = transcript_df[transcript_df['transcript_index'] >= first_question_tid]
    qna_text = "\n".join((qna_df['speaker_type'] + ": " + qna_df['transcript']).values.tolist())
    qna_context = f"This is the QnA text from earnings transcript between management and analysts.\n\n{qna_text}"

    query = "Extract and summarize the whole transcript."
    prompt = f"{management_context}\n\n{qna_context}\n\n{query}"
    summary = fetch_response(prompt=prompt).text

    return summary


def extract_revenue_profit_highlights(transcript_df: pd.DataFrame) -> dict[str, str]:
    # Filter the text discussed by management and extract the highlights, if any
    first_question_tid = transcript_df[transcript_df['speaker_type'] == 'Question']['transcript_index'].min()
    management_df = transcript_df[transcript_df['transcript_index'] < first_question_tid]
    management_df = management_df[management_df['speaker_type'] == 'Management']
    management_text = '\n'.join(transcript_df['transcript'].values.tolist())
    management_context = f"This is the text from earnings transcript as told by management.\n\n{management_text}"
    query = "Extract and summarize the revenue/profit highlights if discussed anywhere."
    prompt = f"{management_context}\n\n{query}"
    management_highlight = fetch_response(prompt=prompt).text

    # Filter the text discussed witihn Q&A and extract the highlights, if any
    qna_df = transcript_df[transcript_df['transcript_index'] >= first_question_tid]
    qna_text = "\n".join((qna_df['speaker_type'] + ": " + qna_df['transcript']).values.tolist())
    qna_context = f"This is the QnA text from earnings transcript between management and analysts.\n\n{qna_text}"
    query = "Extract and summarize the revenue/profit highlights from QnA if discussed anywhere."
    prompt = f"{management_context}\n\n{qna_context}\n\n{query}"
    qna_highlight = fetch_response(prompt=prompt).text

    return {
        'management': management_highlight,
        'qna': qna_highlight
    }


def extract_management_commentary(transcript_df: pd.DataFrame) -> str:
    # Filter the text discussed by management and extract the highlights, if any
    first_question_tid = transcript_df[transcript_df['speaker_type'] == 'Question']['transcript_index'].min()
    management_df = transcript_df[transcript_df['transcript_index'] < first_question_tid]
    management_df = management_df[management_df['speaker_type'] == 'Management']
    management_text = '\n'.join(transcript_df['transcript'].values.tolist())
    management_context = f"This is the text from earnings transcript as told by management.\n\n{management_text}"
    query = "Extract and summarize the management commentary."
    prompt = f"{management_context}\n\n{query}"
    management_commentary = fetch_response(prompt=prompt).text
    return management_commentary


def extract_guidance_outlook(transcript_df: pd.DataFrame) -> dict[str, str]:
    # Filter the text discussed by management and extract the highlights, if any
    first_question_tid = transcript_df[transcript_df['speaker_type'] == 'Question']['transcript_index'].min()
    management_df = transcript_df[transcript_df['transcript_index'] < first_question_tid]
    management_df = management_df[management_df['speaker_type'] == 'Management']
    management_text = '\n'.join(transcript_df['transcript'].values.tolist())
    management_context = f"This is the text from earnings transcript as told by management.\n\n{management_text}"
    query = "Extract and summarize the guidance/outlook if discussed anywhere."
    prompt = f"{management_context}\n\n{query}"
    management_summary = fetch_response(prompt=prompt).text

    # Filter the text discussed witihn Q&A and extract the highlights, if any
    qna_df = transcript_df[transcript_df['transcript_index'] >= first_question_tid]
    qna_text = "\n".join((qna_df['speaker_type'] + ": " + qna_df['transcript']).values.tolist())
    qna_context = f"This is the QnA text from earnings transcript between management and analysts.\n\n{qna_text}"
    query = "Extract and summarize the guidance/outlook from QnA if discussed anywhere."
    prompt = f"{management_context}\n\n{qna_context}\n\n{query}"
    qna_summary = fetch_response(prompt=prompt).text

    return {
        'management': management_summary,
        'qna': qna_summary
    }


def extract_qna_key_points(transcript_df: pd.DataFrame) -> str:
    # Filter the text discussed witihn Q&A and extract the highlights, if any
    first_question_tid = transcript_df[transcript_df['speaker_type'] == 'Question']['transcript_index'].min()
    qna_df = transcript_df[transcript_df['transcript_index'] >= first_question_tid]
    qna_text = "\n".join((qna_df['speaker_type'] + ": " + qna_df['transcript']).values.tolist())
    qna_context = f"This is the QnA text from earnings transcript between management and analysts.\n\n{qna_text}"
    query = "Extract and summarize the key points from QnA."
    prompt = f"{qna_context}\n\n{query}"
    qna_summary = fetch_response(prompt=prompt).text
    return qna_summary
