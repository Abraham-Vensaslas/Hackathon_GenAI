from dotenv import load_dotenv
load_dotenv() ## load all the environemnt variables

import streamlit as st
import os
import sqlite3

import google.generativeai as genai
## Configure Genai Key

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

## Function To Load Google Gemini Model and provide queries as response

def get_gemini_response(question,prompt):
    

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([prompt[0],question])


    return response.text

## Fucntion To retrieve query from the database

def read_sql_query(sql,db):
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    cur.execute(sql)
    rows=cur.fetchall()
    conn.commit()
    conn.close()
    for row in rows:
        print(row)
    return rows

## Define Your Prompt
## Define Your Prompt
prompt = [
    """
    You are an expert in converting English questions to SQL queries!
    The SQL database consists of three tables that contain details about professional football players. These tables can be joined using the unique column `player_id`. Here’s a brief description of the tables:

    ### 1. player_details
    Contains personal and basic details about the players.  
    Columns:  
    - `player_id`: Unique identifier to join across tables  
    - `Name`, `Nationality`, `National_Position`, `National_Kit`, `Height`, `Weight`, `Preferred_Foot`, `Birth_Date`, `Age`, `Preferred_Position`

    ### 2. club_details
    Contains details about the clubs where players are contracted.  
    Columns:  
    - `player_id`: Unique identifier to join across tables  
    - `Club`, `Club_Position`, `Club_Kit`, `Club_Joining`, `Contract_Expiry`

    ### 3. player_stats
    Contains player performance statistics.  
    Columns include:  
    - `player_id`: Unique identifier to join across tables  
    - `Work_Rate`, `Weak_Foot`, `Skill_Moves`, `Ball_Control`, `Dribbling`, `Marking`, `Sliding_Tackle`, `Standing_Tackle`, `Aggression`, `Reactions`, `Attacking_Position`, `Interceptions`, `Vision`, `Composure`, `Crossing`, `Short_Pass`, `Long_Pass`, `Acceleration`, `Speed`, `Stamina`, `Strength`, `Balance`, `Agility`, `Jumping`, `Heading`, `Shot_Power`, `Finishing`, `Long_Shots`, `Curve`, `Freekick_Accuracy`, `Penalties`, `Volleys`, `GK_Positioning`, `GK_Diving`, `GK_Kicking`, `GK_Handling`, `GK_Reflexes`

    ### Instructions:
    You can write SQL queries based on user questions. The required tables can be joined using `player_id`, but some queries may not need joins if the information is available in a single table. Below are some example queries and explanations.
    The query should not have markdown-style formatting ( ```sql and ```) wrapped around the SQL statement. 
    ---

    ### Examples:

    #### Example 1: How many records are present in the `player_details` table?
    SQL Query:  
    SELECT COUNT(*) FROM player_details;

    #### Example 2: Tell me all the players with a Dribbling skill greater than 90.
    SQL Query:  
    SELECT a.Name, b.Dribbling  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    WHERE b.Dribbling > 90;

    #### Example 3: Which clubs have players with more than 80 in Ball Control?
    SQL Query:  
    SELECT c.Club, a.Name, b.Ball_Control  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    JOIN club_details c ON a.player_id = c.player_id  
    WHERE b.Ball_Control > 80;

    #### Example 4: Get the players whose Contract Expiry is within the next year and have an Age greater than 30.
    SQL Query:  
    SELECT a.Name, c.Club, c.Contract_Expiry, a.Age  
    FROM player_details a  
    JOIN club_details c ON a.player_id = c.player_id  
    WHERE c.Contract_Expiry BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 1 YEAR)  
    AND a.Age > 30;

    #### Example 5: What is the average `Strength` of players by their `Nationality`?
    SQL Query:  
    SELECT a.Nationality, AVG(b.Strength) AS Average_Strength  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    GROUP BY a.Nationality;

    #### Example 6: Which players have played for the longest period in a club (sorted by `Club_Joining`)?
    SQL Query:  
    SELECT a.Name, c.Club, c.Club_Joining, DATEDIFF(CURDATE(), c.Club_Joining) AS Years_Played  
    FROM player_details a  
    JOIN club_details c ON a.player_id = c.player_id  
    ORDER BY Years_Played DESC;

    #### Example 7: Get the top 5 players with the highest `Finishing` skills, along with their club and position.
    SQL Query:  
    SELECT a.Name, b.Finishing, c.Club, c.Club_Position  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    JOIN club_details c ON a.player_id = c.player_id  
    ORDER BY b.Finishing DESC  
    LIMIT 5;

    #### Example 8: Find the players who have a better `Weak_Foot` rating than their `Preferred_Foot` (where `Weak_Foot` > `Preferred_Foot`).
    SQL Query:  
    SELECT a.Name, b.Weak_Foot, b.Preferred_Foot  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    WHERE b.Weak_Foot > b.Preferred_Foot;

    #### Example 9: List all players who are good at both `Dribbling` and `Marking` (both > 80).
    SQL Query:  
    SELECT a.Name, b.Dribbling, b.Marking  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    WHERE b.Dribbling > 80 AND b.Marking > 80;

    #### Example 10: Which clubs have players with a `Speed` higher than 90, and how many players per club have this skill?
    SQL Query:  
    SELECT c.Club, COUNT(a.player_id) AS NumberOfPlayers  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    JOIN club_details c ON a.player_id = c.player_id  
    WHERE b.Speed > 90  
    GROUP BY c.Club;

    #### Example 11: Which players have the highest `Stamina` but are currently playing in a club with a `Contract_Expiry` before this year?
    SQL Query:  
    SELECT a.Name, b.Stamina, c.Club, c.Contract_Expiry  
    FROM player_details a  
    JOIN player_stats b ON a.player_id = b.player_id  
    JOIN club_details c ON a.player_id = c.player_id  
    WHERE c.Contract_Expiry < CURDATE()  
    ORDER BY b.Stamina DESC  
    LIMIT 1;

    ---

    ### Notes:
    - The queries above are just examples. Depending on the user's query, you may need to choose which tables to join or use a single table for information.
    - For more advanced queries, make use of aggregate functions like `AVG()`, `SUM()`, `COUNT()`, and filtering with `HAVING` to limit results after grouping.
    - Use `JOIN` to combine tables where necessary, but be mindful of the columns involved to ensure accurate results.
    -  Also the sql code should not have ``` in beginning or end and sql word in output
    """
]

## Streamlit App

st.set_page_config(page_title="Professional Football Player details tracker")
st.header("Gemini App To Retrieve SQL Data")

question=st.text_input("Input: ",key="input")

submit=st.button("Ask the question")

# if submit is clicked
if submit:
    response=get_gemini_response(question,prompt)
    print(response)
    response=read_sql_query(response,"football_player_details.db")
    st.subheader("The response is")
    for row in response:
        print(row)
        st.header(row)