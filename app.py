"""Please Note: I am facing some version related issue while accessing openai. I have tried different methods and different versions of api to fix this but due to time constraint i am using gemini api"""


from dotenv import load_dotenv
load_dotenv() ## load all the environemnt variables

import streamlit as st
import os
import sqlite3
import openai
import google.generativeai as genai
## Configure Genai Key
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


######
from phi.agent import Agent
from phi.model.openai import OpenAIChat
from phi.model.groq import Groq
from phi.tools.duckduckgo import DuckDuckGo


conversation_history = []

## Function To Load Google Gemini Model and provide queries as response

def clean_sql_query(response_text):
    """
    Cleans the SQL query by removing markdown-style formatting.
    """
    # Remove markdown formatting (` ```sql ... ``` `)
    cleaned_query = response_text.replace("```sql", "").replace("```", "").strip()
    return cleaned_query


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
    The SQL database consists of three tables that contain details about customers, their personal information, contact details, and transaction history. These tables can be joined using the unique column `Id`. Below is a brief description of the tables:

    ### 1. Personal_details
    This table contains personal details of the customers.  
    Columns:  
    - `Id`: Unique identifier to join across tables  
    - `Name`: Full name of the customer  
    - `Age`: Age of the customer  
    - `Gender`: Gender of the customer  
    - `Income`: Income category (e.g., Low, High)

    ### 2. Contact_details
    This table contains contact and address information of the customers.  
    Columns:  
    - `Id`: Unique identifier to join across tables  
    - `Email`: Email address of the customer  
    - `Phone`: Phone number  
    - `Address`: Street address  
    - `City`, `State`, `Zipcode`, `Country`: Location details

    ### 3. Transaction_details
    This table contains transaction records of the customers.  
    Columns:  
    - `Id`: Unique identifier to join across tables  
    - `Customer_Segment`: Segment of the customer (e.g., Regular, Premium)  
    - `Date`, `Year`, `Month`, `Time`: Date and time of the transaction  
    - `Total_Purchases`: Number of purchases made in a transaction  
    - `Amount`: Amount per purchase  
    - `Total_Amount`: Total amount spent in the transaction  
    - `Product_Category`, `Product_Brand`, `Product_Type`: Details of the product  
    - `Feedback`: Feedback provided by the customer  
    - `Shipping_Method`, `Payment_Method`, `Order_Status`: Transaction-related attributes  
    - `Ratings`: Customer ratings  
    - `products`: Description of the purchased products

    ---

    ### Instructions:
    You will receive English questions related to customer details, contact information, and transaction history. Convert them into SQL queries based on the following guidelines:
    - Use `JOIN` to combine tables where necessary, but keep the query optimized by selecting only the required columns.
    - Use advanced SQL techniques like subqueries, window functions, and Common Table Expressions (CTEs) where appropriate.
    - Use appropriate filters such as `WHERE`, `GROUP BY`, and `ORDER BY` to ensure accurate results.
    - Avoid markdown-style formatting (```sql and ```) in the SQL query output.

    ---

    ### Advanced Examples:

    #### Example 1: Find the top 5 customers with the highest total spending in 2023, along with their email addresses and total number of transactions.
    SQL Query:  
    WITH TotalSpending AS (  
        SELECT a.Id, a.Name, c.Email, SUM(b.Total_Amount) AS Total_Spent, COUNT(b.Id) AS Transaction_Count  
        FROM Personal_details a  
        JOIN Transaction_details b ON a.Id = b.Id  
        JOIN Contact_details c ON a.Id = c.Id  
        WHERE b.Year = 2023  
        GROUP BY a.Id, a.Name, c.Email  
    )  
    SELECT Name, Email, Total_Spent, Transaction_Count  
    FROM TotalSpending  
    ORDER BY Total_Spent DESC  
    LIMIT 5;

    #### Example 2: Find the most frequently purchased product category by each customer and their total spending in that category.
    SQL Query:  
    WITH CategorySpending AS (  
        SELECT a.Id, a.Name, b.Product_Category, SUM(b.Total_Amount) AS Category_Spending  
        FROM Personal_details a  
        JOIN Transaction_details b ON a.Id = b.Id  
        GROUP BY a.Id, a.Name, b.Product_Category  
    ),  
    RankedCategories AS (  
        SELECT *, RANK() OVER (PARTITION BY Id ORDER BY Category_Spending DESC) AS Rank  
        FROM CategorySpending  
    )  
    SELECT Name, Product_Category, Category_Spending  
    FROM RankedCategories  
    WHERE Rank = 1;

    #### Example 3: Identify customers who have given "Excellent" feedback and spent more than $1000 across all transactions in 2023.
    SQL Query:  
    SELECT a.Name, c.Email, SUM(b.Total_Amount) AS Total_Spent  
    FROM Personal_details a  
    JOIN Transaction_details b ON a.Id = b.Id  
    JOIN Contact_details c ON a.Id = c.Id  
    WHERE b.Year = 2023 AND b.Feedback = 'Excellent'  
    GROUP BY a.Name, c.Email  
    HAVING SUM(b.Total_Amount) > 1000;

    #### Example 4: Calculate the average number of purchases made by customers in each customer segment and gender.
    SQL Query:  
    SELECT b.Customer_Segment, a.Gender, AVG(b.Total_Purchases) AS Avg_Purchases  
    FROM Personal_details a  
    JOIN Transaction_details b ON a.Id = b.Id  
    GROUP BY b.Customer_Segment, a.Gender;

    #### Example 5: Find customers who purchased at least two different product categories in a single transaction in the last year.
    SQL Query:  
    WITH CategoryCount AS (  
        SELECT a.Id, a.Name, b.Date, COUNT(DISTINCT b.Product_Category) AS Category_Count  
        FROM Personal_details a  
        JOIN Transaction_details b ON a.Id = b.Id  
        WHERE b.Year = YEAR(CURDATE()) - 1  
        GROUP BY a.Id, a.Name, b.Date  
    )  
    SELECT Name, Date, Category_Count  
    FROM CategoryCount  
    WHERE Category_Count >= 2;

    #### Example 6: Find the average feedback rating for each shipping method by product category.
    SQL Query:  
    SELECT b.Product_Category, b.Shipping_Method, AVG(b.Ratings) AS Avg_Rating  
    FROM Transaction_details b  
    GROUP BY b.Product_Category, b.Shipping_Method  
    ORDER BY Avg_Rating DESC;

    #### Example 7: Identify customers who have had an order in "Processing" status for more than 30 days.
    SQL Query:  
    SELECT a.Name, c.Email, b.Date, b.Order_Status  
    FROM Personal_details a  
    JOIN Transaction_details b ON a.Id = b.Id  
    JOIN Contact_details c ON a.Id = c.Id  
    WHERE b.Order_Status = 'Processing' AND DATEDIFF(CURDATE(), b.Date) > 30;

    ---

    ### Notes:
    - For advanced queries, consider using window functions, recursive queries, and subqueries where necessary.
    - Always ensure the SQL syntax is correct and that queries are optimized for performance.

    """
]

web_agent = Agent(
    name="Web Agent",
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[DuckDuckGo()],
    instructions=["Always include sources, provide only 2 points about it"],
    show_tool_calls=True,
    markdown=True
)

# Function to trigger the web agent for a query when SQL results are not useful
def use_web_agent_for_search(query):
    # Call the web agent with the user's query
    response = web_agent.print_response(query, stream=True)
    return response






def interact_with_user_gemini(question, db_result):
    """
    This function uses the Google Gemini model to generate a conversational response 
    based on the user question and database query result, while maintaining conversation context.
    If the result is invalid, it invokes the Web Agent to perform a web search.
    """
    # If db_result is empty or invalid, trigger web search
    if not db_result:
        # Use the web agent to get an answer via web search
        web_search_response = use_web_agent_for_search(question)
        conversational_response = f"Web search result: {web_search_response}"
    else:
        # Append the question and DB result to the conversation history
        interaction_prompt = f"""
        You are an AI assistant interacting with users. 
        The user asked: '{question}'. 
        The database result is: '{db_result}'. 
        Create a meaningful and conversational response for the user. Be concise and user-friendly.
        """

        # Update the conversation history
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": db_result})

        # Join all conversation history into a single string to provide context to Gemini
        conversation_context = "\n".join([f"{entry['role']}: {entry['content']}" for entry in conversation_history])

        # Send the full conversation history as the prompt
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content([interaction_prompt, conversation_context])

            # Append the assistant's response to the conversation history
            assistant_response = response.text.strip()
            conversation_history.append({"role": "assistant", "content": assistant_response})

            conversational_response = assistant_response
        except Exception as e:
            conversational_response = f"Error generating response: {e}"

    return conversational_response


## Streamlit App
st.set_page_config(page_title="User Data reports generation")
st.header("Your AI powered Query-Mate")

# Initialize session state for conversation history if it doesn't exist
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Display the chat conversation (history)
for entry in st.session_state.conversation_history:
    if entry["role"] == "user":
        st.markdown(f"**User:** {entry['content']}")
    else:
        st.markdown(f"**Assistant:** {entry['content']}")

# Text input for the user to ask questions
question = st.text_input("Ask a question:", key="input")

# Button to submit the question
submit = st.button("Submit")


if submit:
    


    # Execute the cleaned query
    try:
        # Get the response from Gemini
        raw_response = get_gemini_response(question, prompt)
        print("Raw Response from Gemini:", raw_response)

        # Clean the SQL query
        cleaned_query = clean_sql_query(raw_response)
        print("Cleaned SQL Query:", cleaned_query)
        query_result  = read_sql_query(cleaned_query, "Retail_details.db")

        print(query_result)
        
        # Format the response for display
        if query_result and len(query_result) == 1 and len(query_result[0]) == 1:
            # Extract the single result value from the tuple
            result_value = query_result[0][0]
            
            # Generate a dynamic message based on the question
            conversational_response = interact_with_user_gemini(question, result_value)
            #Update the session state with the new conversation history
            st.session_state.conversation_history.append({"role": "user", "content": question})
            st.session_state.conversation_history.append({"role": "assistant", "content": conversational_response})

            st.markdown(f"**Assistant:** {conversational_response}")
        elif len(query_result) > 1:     
            result_value = query_result       
            # Generate a dynamic message based on the question
            conversational_response = interact_with_user_gemini(question, result_value)
            #Update the session state with the new conversation history
            st.session_state.conversation_history.append({"role": "user", "content": question})
            st.session_state.conversation_history.append({"role": "assistant", "content": conversational_response})

            st.markdown(f"**Assistant:** {conversational_response}")
        else:
            conversational_response = interact_with_user_gemini(question, None)
            st.session_state.conversation_history.append({"role": "user", "content": question})
            st.session_state.conversation_history.append({"role": "assistant", "content": conversational_response})

            st.markdown(f"**Assistant:** {conversational_response}")
            
    except sqlite3.OperationalError as e:
        # If SQL result is empty or doesn't fit expected format, use Web Agent
        conversational_response = interact_with_user_gemini(question, None)
        st.session_state.conversation_history.append({"role": "user", "content": question})
        st.session_state.conversation_history.append({"role": "assistant", "content": conversational_response})

        st.markdown(f"**Assistant:** {conversational_response}")

