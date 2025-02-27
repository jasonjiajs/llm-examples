from openai import OpenAI
import pandas as pd
import numpy as np
import os
import json
import streamlit as st

# Read the data
@st.cache_data(show_spinner=False)
def read_data(filepath):
    df_full = pd.read_csv(filepath, encoding='ISO-8859-1')
    if 'relevance_problem' in df_full.columns:
        print('Data with labels generated by GPT loaded')
        df = df_full[['problem', 'solution', 'relevance_problem', 'clarity_problem', 'suitability_solution', 'clarity_solution']]
        contains_labels = True
    else:
        print('Data loaded')
        df = df_full[['problem', 'solution']]
        contains_labels = False
    return df_full, df, contains_labels

def get_response(client, system_content, user_content, finetuned=False):
    if finetuned:
        model = 'ft:gpt-3.5-turbo-1106:personal::8e9YXb9p'
    else:
        model = "gpt-3.5-turbo-1106"
    response = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
            ],
        temperature=0,
        seed=0
    )
    return json.loads(response.choices[0].message.content)

def get_metrics(df_dict, client, system_content, finetuned):
    response_list = []
    for i in range(len(df_dict)):
        user_content = str(df_dict[i])
        response = get_response(client, system_content, user_content, finetuned)
        response_list.append(response)

    df_metrics = pd.DataFrame(response_list)
    return df_metrics

def get_metrics_for_filtering_ideas(df_full, df, client, finetuned=True):
    df_dict = df.to_dict(orient='records') # Process df into list of dictionaries
    system_content = "You are a venture capital expert evaluating potential circular economy startup pitches. \
    Mark the startup idea (problem and solution) \
    from 1 to 3 in integer numbers (where 1 is bad, 2 is okay, and 3 is good) \
    in each of four criteria: \
    relevance of the problem to the circular economy (relevance_problem), \
    clarity of the problem (clarity_problem), \
    suitability of solution to the problem (suitability_solution) and \
    clarity of the solution (clarity_solution). \
    Return the following fields in a JSON dict: \
    'relevance_problem', 'clarity_problem', 'suitability_solution' and 'clarity_solution'."
    df_metrics = get_metrics(df_dict, client, system_content, finetuned)
    df_metrics = pd.concat([df_full, df_metrics], axis=1)
    df_metrics['overall_score'] = df_metrics[['relevance_problem', 'clarity_problem', 'suitability_solution', 'clarity_solution']].mean(axis=1)
    return df_metrics