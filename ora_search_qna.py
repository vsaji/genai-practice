import streamlit as st
import os
import oracledb
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine
from sqlalchemy import text
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_core.messages import SystemMessage
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

class OracleSearch:

    def __init__(self):
        load_dotenv()
        user = os.environ.get('ORA_USER')
        cs = os.environ.get('ORA_CS')
        pw = os.environ.get('ORA_PWD')

        print(f"User: {user}, Connection String: {cs}")

        engine = create_engine(
        f'oracle+oracledb://:@',
        connect_args={
            "user": user,
            "password": pw,
            "dsn": cs
        })

        db = SQLDatabase(engine)
        print(db.dialect)
        print(db.get_usable_table_names())
        db.run("SELECT count(*) FROM rates")

        llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        #    max_tokens=None,
        #    timeout=None,
        #    max_retries=2,
        )
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        tools = toolkit.get_tools()

        SQL_PREFIX = """You are an agent designed to interact with an Oracle SQL database.
        Given an input question, user the Table_Relationships provide below to create a syntactically correct Oracle SQL query to run, then look at the results of the query and return the answer.
        Unless the user specifies a specific number of rows, always limit your query to at most 5 results.
        You have access to tools for interacting with the database.
        You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        You will use only tables provided in Table_Relationships for quering the result
        If the question contains trade then include trade table in the join
        
        Table_Relationships
        table: RATES = [("Column Name":"RATE_ID","Description":"Rate Id","Type":"NUMBER"),("Column Name":"DEAL_ID","Description":"Deal Id refers to table DEAL and column DEAL_ID","Type":"NUMBER(22,0)"),("Column Name":"PRIORITY","Description":"Priority (1 is highest)","Type":"NUMBER(22,0)"),("Column Name":"PRODUCT_TYPE","Description":"Product Type","Type":"VARCHAR2(10 BYTE)"),("Column Name":"SUB_PRODUCT_TYPE","Description":"Product Sub type","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"COUNTRY","Description":"Country  Code","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CMSN_TYPE","Description":"Commission Type (cps=cents per share, bps=basis points)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CMSN_MIN","Description":"Minimum Commission","Type":"NUMBER(22,0)"),("Column Name":"CMSN_MAX","Description":"Maximum Commission","Type":"NUMBER(22,0)"),("Column Name":"TRADE_AREA","Description":"Trade Area","Type":"VARCHAR2(20 BYTE)"),("Column Name":"REGION","Description":"Region (NAM=North America,EMEA=EUROPE,APAC=Asiapac,UK=United Kingdom)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"GP_NUM","Description":"Grandparent number","Type":"VARCHAR2(10 BYTE)"),("Column Name":"PRICE_MIN","Description":"Minimum Price","Type":"NUMBER(22,0)",("Column Name":"PRICE_MAX","Description":"Maximum Price","Type":"NUMBER(22,0)"),("Column Name":"SIDE","Description":"Side (S=Sell, B=Buy)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"QUANTITY_MIN","Description":"Minimum Quantity","Type":"NUMBER(22,0)"),("Column Name":"QUANTTITY_MAX","Description":"Maximum Quantity","Type":"NUMBER(22,0)"),("Column Name":"RSCH_TYPE","Description":"Research Fee Type (cps=cents per share, bps=basis points, rate=1 indicates 100%)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"RSCH_FEE","Description":"Research Fee","Type":"NUMBER(22,0)"),("Column Name":"EXEC_TYPE","Description":"Execution Fee Type (cps=cents per share, bps=basis points)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"EXEC_FEE","Description":"Execution Fee","Type":"NUMBER(22,0)"),("Column Name":"BEGIN_DATE","Description":"Effective from","Type":"DATE"),("Column Name":"END_DATE","Description":"Effective till","Type":"DATE"),("Column Name":"STATUS","Description":"Status (1 is active, > 1 is not active)","Type":"NUMBER(22,0)"),("Column Name":"COMMENTS","Description":"User comments","Type":"VARCHAR2(255 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated time","Type":"TIMESTAMP(6)"),("Column Name":"LAST_UPDATE_USER","Description":"Last Updated user","Type":"VARCHAR2(255 BYTE)")]
        table: CLIENT = [("Column Name":"CLIENT_ID","Description":"Client ID ","Type":"NUMBER"),("Column Name":"GP_NUM","Description":"Grandparent Number","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CLIENT_NAME","Description":"Client Name","Type":"VARCHAR2(10 BYTE)"),("Column Name":"PAYMENT_FREQUENCY","Description":"Payment Frequency (1=Monthly,2=Yearly)","Type":"NUMBER"),("Column Name":"LAST_MODIFIED_USER","Description":"Last Updated time","Type":"VARCHAR2(20 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated user","Type":"TIMESTAMP(6)")]
        table: DEAL = [("Column Name":"DEAL_ID","Description":"Deal Id","Type":"NUMBER"),("Column Name":"DEAL_MNC","Description":"Deal Mnemonic","Type":"VARCHAR2(20 BYTE)"),("Column Name":"DEAL_TYPE","Description":"Deal Type(1=Regular,4=Classic,2=Partial,3=Full)","Type":"NUMBER(3,0)"),("Column Name":"CLIENT_ID","Description":"Client Id refers to the table CLIENT and column CLIENT_ID","Type":"NUMBER(10,0)"),("Column Name":"STATUS","Description":"Status (1 is active, > 1 is not active)","Type":"NUMBER(3,0)"),("Column Name":"COST_CENTER","Description":"Cost Center","Type":"NUMBER(3,0)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR2(20 BYTE)"),("Column Name":"DEFAULT_DEAL","Description":"Default Deal","Type":"NUMBER(1,0)"),("Column Name":"ELIGIBLE_CAPACITY","Description":"Eligible Capacity","Type":"NUMBER(3,0)"),("Column Name":"DEFICIT_THRESHOLD","Description":"Deficit Thresholdd Floa","Type":"FLOAT"),("Column Name":"BEGIN_DATE","Description":"Begin Dated Date","Type":"DATE"),("Column Name":"NOTES","Description":"Notes","Type":"VARCHAR2(250 BYTE)"),("Column Name":"BUNDLED_FLAG","Description":"Bundled Flag","Type":"NUMBER(1,0)"),("Column Name":"CSA_CONNECT_MAKER_CHECKER","Description":"CSA Connect Maker","Type":"NUMBER(1,0)"),("Column Name":"INVOICE_APPROVER_ELIGIBLE","Description":"Invoice Approver","Type":"NUMBER(1,0)"),("Column Name":"DEAL_ASSOCIATE","Description":"Deal Associate","Type":"VARCHAR2(10 BYTE)"),("Column Name":"DEAL_MANAGER","Description":"Deal Manager","Type":"VARCHAR2(10 BYTE)"),("Column Name":"LAST_MODIFIED_USER","Description":"Last Modified User","Type":"VARCHAR2(10 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated Time","Type":"TIMESTAMP(6)")]
        table: TRADE = [("Column Name":"TRADE_ID","Description":"Unique Id of the trade table","Type":"NUMBER GENERATED BY DEFAULT AS IDENTITY"),("Column Name":"DEAL_ID","Description":"Deal Id refers to the table DEAL and column DEAL_ID","Type":"NUMBER NOT NULL"),("Column Name":"RATE_ID","Description":"Rate Id refers to the table RATES and column RATE_ID","Type":"NUMBER NOT NULL"),("Column Name":"TRADEDATE","Description":"Trade Date","Type":"DATE"),("Column Name":"PRODUCT_TYPE","Description":"Product Type","Type":"VARCHAR(10)"),("Column Name":"SUB_PRODUCT_TYPE","Description":"Product Sub type","Type":"VARCHAR(10)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR(10)"),("Column Name":"COUNTRY","Description":"Country  Code","Type":"VARCHAR(10)"),("Column Name":"GROSS_BPS","Description":"Gross amount in bps","Type":"NUMBER"),("Column Name":"GROSS_CPS","Description":"Gross amount in cps","Type":"NUMBER"),("Column Name":"TRADE_AREA","Description":"Trading area","Type":"VARCHAR(10)"),("Column Name":"REGION","Description":"Region (NAM,APAC,EMEA)","Type":"VARCHAR(10)"),("Column Name":"GP_NUM","Description":"Grandparent number","Type":"NUMBER"),("Column Name":"PRICE","Description":"Price","Type":"NUMBER"),("Column Name":"SIDE","Description":"Side (b=buy,s=sell)","Type":"VARCHAR(1)"),("Column Name":"QUANTITY","Description":"Trading quantity","Type":"NUMBER"),("Column Name":"PRIN_AMOUNT","Description":"","Type":"NUMBER"),("Column Name":"GROSS_COMMISSION","Description":"Gross Commission","Type":"NUMBER"),("Column Name":"EXECUTION_COMMISSION","Description":"Execution commission","Type":"NUMBER"),("Column Name":"RESEARCH_COMMISSION","Description":"Research Commission","Type":"NUMBER"),("Column Name":"CSA_STATUS","Description":"CSA status (1 =active, 0=inactive)","Type":"NUMBER"),("Column Name":"EXCEPTION_CODE","Description":"Exception code","Type":"NUMBER"),("Column Name":"HARD_CODED_RATE_FLAG","Description":"Hard Coded Rate flag (1=hard coded)","Type":"NUMBER"),("Column Name":"HARD_CODED_RATE","Description":"Hard coded rate indicate the overriden date by the user","Type":"NUMBER"),("Column Name":"HARD_CODE_RATE_TYPE","Description":"Hard coded rate type (cps or bps)","Type":"VARCHAR(10)"),("Column Name":"LAST_UPDATE_USER","Description":"User who modified this record","Type":"VARCHAR2(50)"),("Column Name":"LAST_UPDATE_TIME","Description":"Time when the user modified the record","Type":"TIMESTAMP(6)")]
        Relationship : RATES.DEAL_ID = DEAL.DEAL_ID
        Relationship : DEAL.CLIENT_ID = CLIENT.CLIENT_ID
        Relationship : TRADE.DEAL_ID = DEAL.DEAL_ID
        Relationship : TRADE.RATE_ID = RATES.RATE_ID

        When possible try to join tables to extend the retrieved information.
        Suppress results if the value is -1
        Use uppercase function while evaluating client name,research type, region, execution type, country and currency in the query.
        If the result contains numbers only, then list the numbers in a tabular format.
        If the query returns empty row, then return a message indicating that no results were found.
        # """

        # SQL_PREFIX = """You are an agent designed to interact with an Oracle SQL database.
        # Given an input question, create a syntactically correct Oracle SQL query to run, then look at the results of the query and return the answer.
        # Unless the user specifies a specific number of rows, always limit your query to at most 5 results.
        # You have access to tools for interacting with the database.
        # You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        # Don't query database for table schema. You will use only the following tables for quering the result : RATES,CLIENT,DEAL,TRADE
        # Following are the schema of the tables. 
        # table: RATES = [("Column Name":"RATE_ID","Description":"Rate Id","Type":"NUMBER"),("Column Name":"DEAL_ID","Description":"Deal Id refers to table DEAL and column DEAL_ID","Type":"NUMBER(22,0)"),("Column Name":"PRIORITY","Description":"Priority (1 is highest)","Type":"NUMBER(22,0)"),("Column Name":"PRODUCT_TYPE","Description":"Product Type","Type":"VARCHAR2(10 BYTE)"),("Column Name":"SUB_PRODUCT_TYPE","Description":"Product Sub type","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"COUNTRY","Description":"Country  Code","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CMSN_TYPE","Description":"Commission Type (cps=cents per share, bps=basis points)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CMSN_MIN","Description":"Minimum Commission","Type":"NUMBER(22,0)"),("Column Name":"CMSN_MAX","Description":"Maximum Commission","Type":"NUMBER(22,0)"),("Column Name":"TRADE_AREA","Description":"Trade Area","Type":"VARCHAR2(20 BYTE)"),("Column Name":"REGION","Description":"Region (NAM=North America,EMEA=EUROPE,APAC=Asiapac,UK=United Kingdom)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"GP_NUM","Description":"Grandparent number","Type":"VARCHAR2(10 BYTE)"),("Column Name":"PRICE_MIN","Description":"Minimum Price","Type":"NUMBER(22,0)",("Column Name":"PRICE_MAX","Description":"Maximum Price","Type":"NUMBER(22,0)"),("Column Name":"SIDE","Description":"Side (S=Sell, B=Buy)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"QUANTITY_MIN","Description":"Minimum Quantity","Type":"NUMBER(22,0)"),("Column Name":"QUANTTITY_MAX","Description":"Maximum Quantity","Type":"NUMBER(22,0)"),("Column Name":"RSCH_TYPE","Description":"Research Fee Type (cps=cents per share, bps=basis points, rate=1 indicates 100%)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"RSCH_FEE","Description":"Research Fee","Type":"NUMBER(22,0)"),("Column Name":"EXEC_TYPE","Description":"Execution Fee Type (cps=cents per share, bps=basis points)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"EXEC_FEE","Description":"Execution Fee","Type":"NUMBER(22,0)"),("Column Name":"BEGIN_DATE","Description":"Effective from","Type":"DATE"),("Column Name":"END_DATE","Description":"Effective till","Type":"DATE"),("Column Name":"STATUS","Description":"Status (1 is active, > 1 is not active)","Type":"NUMBER(22,0)"),("Column Name":"COMMENTS","Description":"User comments","Type":"VARCHAR2(255 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated time","Type":"TIMESTAMP(6)"),("Column Name":"LAST_UPDATE_USER","Description":"Last Updated user","Type":"VARCHAR2(255 BYTE)")]
        # table: CLIENT = [("Column Name":"CLIENT_ID","Description":"Client ID ","Type":"NUMBER"),("Column Name":"GP_NUM","Description":"Grandparent Number","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CLIENT_NAME","Description":"Client Name","Type":"VARCHAR2(10 BYTE)"),("Column Name":"PAYMENT_FREQUENCY","Description":"Payment Frequency (1=Monthly,2=Yearly)","Type":"NUMBER"),("Column Name":"LAST_MODIFIED_USER","Description":"Last Updated time","Type":"VARCHAR2(20 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated user","Type":"TIMESTAMP(6)")]
        # table: DEAL = [("Column Name":"DEAL_ID","Description":"Deal Id","Type":"NUMBER"),("Column Name":"DEAL_MNC","Description":"Deal Mnemonic","Type":"VARCHAR2(20 BYTE)"),("Column Name":"DEAL_TYPE","Description":"Deal Type(1=Regular,4=Classic,2=Partial,3=Full)","Type":"NUMBER(3,0)"),("Column Name":"CLIENT_ID","Description":"Client Id refers to the table CLIENT and column CLIENT_ID","Type":"NUMBER(10,0)"),("Column Name":"STATUS","Description":"Status (1 is active, > 1 is not active)","Type":"NUMBER(3,0)"),("Column Name":"COST_CENTER","Description":"Cost Center","Type":"NUMBER(3,0)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR2(20 BYTE)"),("Column Name":"DEFAULT_DEAL","Description":"Default Deal","Type":"NUMBER(1,0)"),("Column Name":"ELIGIBLE_CAPACITY","Description":"Eligible Capacity","Type":"NUMBER(3,0)"),("Column Name":"DEFICIT_THRESHOLD","Description":"Deficit Thresholdd Floa","Type":"FLOAT"),("Column Name":"BEGIN_DATE","Description":"Begin Dated Date","Type":"DATE"),("Column Name":"NOTES","Description":"Notes","Type":"VARCHAR2(250 BYTE)"),("Column Name":"BUNDLED_FLAG","Description":"Bundled Flag","Type":"NUMBER(1,0)"),("Column Name":"CSA_CONNECT_MAKER_CHECKER","Description":"CSA Connect Maker","Type":"NUMBER(1,0)"),("Column Name":"INVOICE_APPROVER_ELIGIBLE","Description":"Invoice Approver","Type":"NUMBER(1,0)"),("Column Name":"DEAL_ASSOCIATE","Description":"Deal Associate","Type":"VARCHAR2(10 BYTE)"),("Column Name":"DEAL_MANAGER","Description":"Deal Manager","Type":"VARCHAR2(10 BYTE)"),("Column Name":"LAST_MODIFIED_USER","Description":"Last Modified User","Type":"VARCHAR2(10 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated Time","Type":"TIMESTAMP(6)")]
        # table: TRADE = [("Column Name":"TRADE_ID","Description":"Unique Id of the trade table","Type":"NUMBER GENERATED BY DEFAULT AS IDENTITY"),("Column Name":"DEAL_ID","Description":"Deal Id refers to the table DEAL and column DEAL_ID","Type":"NUMBER NOT NULL"),("Column Name":"RATE_ID","Description":"Rate Id refers to the table RATES and column RATE_ID","Type":"NUMBER NOT NULL"),("Column Name":"TRADEDATE","Description":"Trade Date","Type":"DATE"),("Column Name":"PRODUCT_TYPE","Description":"Product Type","Type":"VARCHAR(10)"),("Column Name":"SUB_PRODUCT_TYPE","Description":"Product Sub type","Type":"VARCHAR(10)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR(10)"),("Column Name":"COUNTRY","Description":"Country  Code","Type":"VARCHAR(10)"),("Column Name":"GROSS_BPS","Description":"Gross amount in bps","Type":"NUMBER"),("Column Name":"GROSS_CPS","Description":"Gross amount in cps","Type":"NUMBER"),("Column Name":"TRADE_AREA","Description":"Trading area","Type":"VARCHAR(10)"),("Column Name":"REGION","Description":"Region (NAM,APAC,EMEA)","Type":"VARCHAR(10)"),("Column Name":"GP_NUM","Description":"Grandparent number","Type":"NUMBER"),("Column Name":"PRICE","Description":"Price","Type":"NUMBER"),("Column Name":"SIDE","Description":"Side (b=buy,s=sell)","Type":"VARCHAR(1)"),("Column Name":"QUANTITY","Description":"Trading quantity","Type":"NUMBER"),("Column Name":"PRIN_AMOUNT","Description":"","Type":"NUMBER"),("Column Name":"GROSS_COMMISSION","Description":"Gross Commission","Type":"NUMBER"),("Column Name":"EXECUTION_COMMISSION","Description":"Execution commission","Type":"NUMBER"),("Column Name":"RESEARCH_COMMISSION","Description":"Research Commission","Type":"NUMBER"),("Column Name":"CSA_STATUS","Description":"CSA status (1 =active, 0=inactive)","Type":"NUMBER"),("Column Name":"EXCEPTION_CODE","Description":"Exception code","Type":"NUMBER"),("Column Name":"HARD_CODED_RATE_FLAG","Description":"Hard Coded Rate flag (1=hard coded)","Type":"NUMBER"),("Column Name":"HARD_CODED_RATE","Description":"Hard coded rate indicate the overriden date by the user","Type":"NUMBER"),("Column Name":"HARD_CODE_RATE_TYPE","Description":"Hard coded rate type (cps or bps)","Type":"VARCHAR(10)"),("Column Name":"LAST_UPDATE_USER","Description":"User who modified this record","Type":"VARCHAR2(50)"),("Column Name":"LAST_UPDATE_TIME","Description":"Time when the user modified the record","Type":"TIMESTAMP(6)")]
        # Relationship : RATES.DEAL_ID = DEAL.DEAL_ID
        # Relationship : DEAL.CLIENT_ID = CLIENT.CLIENT_ID
        # Relationship : TRADE.DEAL_ID = DEAL.DEAL_ID
        # Relationship : TRADE.RATE_ID = RATES.RATE_ID
        # DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP, TRUNCATE etc.) to the database.
        # When possible try to join tables to extend the retrieved information.
        # Suppress results if the value is -1
        # Use uppercase function while evaluating client name,research type, region, execution type, country and currency in the query.
        # If the result contains numbers only, then list the numbers in a tabular format.
        # If the query returns empty row, then return a message indicating that no results were found.
        # # """

        # SQL_PREFIX = """You are an agent designed to interact with an Oracle SQL database.
        # Given an input question, create a syntactically correct Oracle SQL query to run, then look at the results of the query and return the answer.
        # Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 5 results.
        # You can order the results by a relevant column to return the most interesting examples in the database.
        # Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        # You have access to tools for interacting with the database.
        # Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        # You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        # DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP, TRUNCATE etc.) to the database.
        # To start you should ALWAYS look at the tables in the database to see what you can query.
        # Do NOT skip this step.
        # When possible try to join tables to extend the retrieved information.
        # Then you should query the schema of the most relevant tables."""

        #Apply case insensitivity by change the column and values to uppercase for nouns in the question while constructing the query.
        #table: RATES = [("Column Name":"RATE_ID","Description":"Rate Id","Type":"NUMBER"),("Column Name":"DEAL_ID","Description":"Deal Id refers to table DEAL and column DEAL_ID","Type":"NUMBER(22,0)"),("Column Name":"PRIORITY","Description":"Priority (1 is highest)","Type":"NUMBER(22,0)"),("Column Name":"PRODUCT_TYPE","Description":"Product Type","Type":"VARCHAR2(10 BYTE)"),("Column Name":"SUB_PRODUCT_TYPE","Description":"Product Sub type","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"COUNTRY","Description":"Country  Code","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CMSN_TYPE","Description":"Commission Type (cps=cents per share, bps=basis points)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CMSN_MIN","Description":"Minimum Commission","Type":"NUMBER(22,0)"),("Column Name":"CMSN_MAX","Description":"Maximum Commission","Type":"NUMBER(22,0)"),("Column Name":"TRADE_AREA","Description":"Trade Area","Type":"VARCHAR2(20 BYTE)"),("Column Name":"REGION","Description":"Region (NAM=North America,EMEA=EUROPE,APAC=Asiapac,UK=United Kingdom)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"GP_NUM","Description":"Grandparent number","Type":"VARCHAR2(10 BYTE)"),("Column Name":"PRICE_MIN","Description":"Minimum Price","Type":"NUMBER(22,0)",("Column Name":"PRICE_MAX","Description":"Maximum Price","Type":"NUMBER(22,0)"),("Column Name":"SIDE","Description":"Side (S=Sell, B=Buy)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"QUANTITY_MIN","Description":"Minimum Quantity","Type":"NUMBER(22,0)"),("Column Name":"QUANTTITY_MAX","Description":"Maximum Quantity","Type":"NUMBER(22,0)"),("Column Name":"RSCH_TYPE","Description":"Research Fee Type (cps=cents per share, bps=basis points, rate=1 indicates 100%)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"RSCH_FEE","Description":"Research Fee","Type":"NUMBER(22,0)"),("Column Name":"EXEC_TYPE","Description":"Execution Fee Type (cps=cents per share, bps=basis points)","Type":"VARCHAR2(10 BYTE)"),("Column Name":"EXEC_FEE","Description":"Execution Fee","Type":"NUMBER(22,0)"),("Column Name":"BEGIN_DATE","Description":"Effective from","Type":"DATE"),("Column Name":"END_DATE","Description":"Effective till","Type":"DATE"),("Column Name":"STATUS","Description":"Status (1 is active, > 1 is not active)","Type":"NUMBER(22,0)"),("Column Name":"COMMENTS","Description":"User comments","Type":"VARCHAR2(255 BYTE)")]
        #table: CLIENT = [("Column Name":"CLIENT_ID","Description":"Client ID ","Type":"NUMBER"),("Column Name":"GP_NUM","Description":"Grandparent Number","Type":"VARCHAR2(10 BYTE)"),("Column Name":"CLIENT_NAME","Description":"Client Name","Type":"VARCHAR2(10 BYTE)"),("Column Name":"PAYMENT_FREQUENCY","Description":"Payment Frequency (1=Monthly,2=Yearly)","Type":"NUMBER"),("Column Name":"LAST_MODIFIED_USER","Description":"Last Updated time","Type":"VARCHAR2(20 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated user","Type":"TIMESTAMP(6)")]
        #table: DEAL = [("Column Name":"DEAL_ID","Description":"Deal Id","Type":"NUMBER"),("Column Name":"DEAL_MNC","Description":"Deal Mnemonic","Type":"VARCHAR2(20 BYTE)"),("Column Name":"DEAL_TYPE","Description":"Deal Type(1=Regular,4=Classic,2=Partial,3=Full)","Type":"NUMBER(3,0)"),("Column Name":"CLIENT_ID","Description":"Client Id refers to the table CLIENT and column CLIENT_ID","Type":"NUMBER(10,0)"),("Column Name":"STATUS","Description":"Status (1 is active, > 1 is not active)","Type":"NUMBER(3,0)"),("Column Name":"COST_CENTER","Description":"Cost Center","Type":"NUMBER(3,0)"),("Column Name":"CURRENCY","Description":"Currency (ISO 3 character code)","Type":"VARCHAR2(20 BYTE)"),("Column Name":"DEFAULT_DEAL","Description":"Default Deal","Type":"NUMBER(1,0)"),("Column Name":"ELIGIBLE_CAPACITY","Description":"Eligible Capacity","Type":"NUMBER(3,0)"),("Column Name":"DEFICIT_THRESHOLD","Description":"Deficit Thresholdd Floa","Type":"FLOAT"),("Column Name":"BEGIN_DATE","Description":"Begin Dated Date","Type":"DATE"),("Column Name":"NOTES","Description":"Notes","Type":"VARCHAR2(250 BYTE)"),("Column Name":"BUNDLED_FLAG","Description":"Bundled Flag","Type":"NUMBER(1,0)"),("Column Name":"CSA_CONNECT_MAKER_CHECKER","Description":"CSA Connect Maker","Type":"NUMBER(1,0)"),("Column Name":"INVOICE_APPROVER_ELIGIBLE","Description":"Invoice Approver","Type":"NUMBER(1,0)"),("Column Name":"DEAL_ASSOCIATE","Description":"Deal Associate","Type":"VARCHAR2(10 BYTE)"),("Column Name":"DEAL_MANAGER","Description":"Deal Manager","Type":"VARCHAR2(10 BYTE)"),("Column Name":"LAST_MODIFIED_USER","Description":"Last Modified User","Type":"VARCHAR2(10 BYTE)"),("Column Name":"LAST_UPDATE_TIME","Description":"Last Updated Time","Type":"TIMESTAMP(6)")]


        system_message = SystemMessage(content=SQL_PREFIX)
        self.agent_executor = create_react_agent(llm, tools, state_modifier=system_message)

    def executeQuery(self, msg):
        response=self.agent_executor.invoke({"messages": [HumanMessage(content=msg)]})
        message = response["messages"][-1]
        #message = response["messages"]
        result=""
    
        for message in response["messages"]:
            message.pretty_print()


        if isinstance(message, dict) and "content" in message:
                # Extract content if it's a dictionary with a "content" key
                result = message["content"]
        elif hasattr(message, 'content'):
            # If it's an object with a "content" attribute
            result = message.content
        elif isinstance(message, str):
            # Handle cases where the message might be a plain string
            result = message
        else:
            # Fall back to pretty-printing or other methods
            result = str(message)
        return result


    def start(self):
        st.title("AI Search for rate card")

        # Input: User enters search query
        search_query = st.text_input("Talk to the AI Agent")

        # Button: User triggers the search
        if st.button("Search"):
            if search_query:
                # Perform the search and get results
                result = self.executeQuery(search_query)
                # Display search results
                try:
                    st.write("AI Output: ")
                    st.write(f"{result}")
                    #st.json(results)
                except Exception as e:
                    print(f"Error: {e}")
                st.divider()


if __name__ == "__main__":
    oraSrch = OracleSearch()
    oraSrch.start()