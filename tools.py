import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List
import chromadb
from openai import OpenAI


TICKET_DB: Dict[str, Any] = {} 

class TicketManagementTool:
    """
    Simulated API for Safar Travel ticket management (Booking, Cancellation, Info).
    """

    def _generate_ticket_id(self, origin: str, destination: str) -> str:
        """Generates a unique, realistic-looking Safar Travel ticket ID."""
        prefix = f"{origin[:2].upper()}{destination[:2].upper()}"
        return f"SF-{prefix}-{uuid.uuid4().hex[:6].upper()}"

    def book_ticket(self, origin_city: str, destination_city: str, travel_date: str, passenger_name: str, national_id: str) -> Dict[str, Any]:
        """
        [Function Calling Tool] Books a ticket in the simulated system.
        Required: Origin, Destination (Iran-only), Date, Name, National ID.
        """
        if not all([origin_city, destination_city, travel_date, passenger_name, national_id]):
            return {"status": "error", "message": "Missing required booking information. Please provide origin city, destination city, travel date, passenger name, and national ID (کد ملی)."}

        try:
            base_price = 1500000  
            if destination_city.lower() in ["kish", "qeshm"]:
                base_price *= 1.5 
            
            travel_times = ["08:00", "14:30", "20:00"]
            ticket_id = self._generate_ticket_id(origin_city, destination_city)
            
            ticket_data = {
                "ticket_id": ticket_id,
                "origin": origin_city,
                "destination": destination_city,
                "travel_date": travel_date,
                "departure_time": travel_times[len(TICKET_DB) % 3], 
                "passenger_name": passenger_name,
                "national_id": national_id,
                "price_irr": base_price,
                "status": "CONFIRMED",
                "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            TICKET_DB[ticket_id] = ticket_data
            
            print(f"DEBUG: Ticket booked - ID: {ticket_id}")
            return {
                "status": "success",
                "message": f"بلیط شما با موفقیت رزرو شد. (Ticket successfully booked).",
                "details": ticket_data
            }

        except Exception as e:
            return {"status": "error", "message": f"An internal error occurred during booking: {str(e)}"}

    def cancel_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        [Function Calling Tool] Cancels an existing reservation and calculates a refund.
        """
        ticket = TICKET_DB.get(ticket_id)
        if not ticket:
            return {"status": "error", "message": f"Ticket ID '{ticket_id}' not found. Please check the ID."}
        
        if ticket["status"] == "CANCELLED":
            return {"status": "info", "message": f"Ticket ID '{ticket_id}' is already cancelled."}

        refund_percentage = 0.70 
        refund_amount = int(ticket["price_irr"] * refund_percentage)
        penalty_amount = ticket["price_irr"] - refund_amount
        
        ticket["status"] = "CANCELLED"
        ticket["cancellation_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        TICKET_DB[ticket_id] = ticket 
        
        print(f"DEBUG: Ticket cancelled - ID: {ticket_id}")
        return {
            "status": "success",
            "message": f"Ticket {ticket_id} has been successfully cancelled. A refund of {refund_amount:,} IRR (70% of price) will be processed. Penalty applied: {penalty_amount:,} IRR.",
            "ticket_id": ticket_id,
            "refund_amount_irr": refund_amount
        }

    def get_ticket_info(self, ticket_id: str) -> Dict[str, Any]:
        """
        [Function Calling Tool] Retrieves detailed information about an existing ticket.
        """
        ticket = TICKET_DB.get(ticket_id)
        if not ticket:
            return {"status": "error", "message": f"Ticket ID '{ticket_id}' not found. Please check the ID."}

        return {
            "status": "success",
            "message": "Ticket information retrieved.",
            "details": ticket
        }


class RAGTool:
    """Retrieval-Augmented Generation (RAG) System using ChromaDB."""
    
    def __init__(self, data_path: str = 'src/data/company_policy.txt'):
        self.client = chromadb.Client()
        self.collection_name = "safar_travel_policies"
        self.collection = self.client.get_or_create_collection(self.collection_name)
        self.data_path = data_path
        self._load_data()

    def _load_data(self):
        """Loads and processes the text file into the vector database."""
        if self.collection.count() > 0:
            print("DEBUG: RAG data already loaded.")
            return

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            documents = [doc.strip() for doc in content.split('\n\n') if doc.strip()]
            
            if not documents:
                print(f"WARNING: RAG data file {self.data_path} is empty.")
                return

            ids = [f"doc_{i}" for i in range(len(documents))]
            
            self.collection.add(
                documents=documents,
                ids=ids
            )
            print(f"DEBUG: Successfully loaded {len(documents)} documents into ChromaDB.")
            
        except FileNotFoundError:
            print(f"ERROR: RAG data file not found at {self.data_path}. RAG tool will not work.")
        except Exception as e:
            print(f"ERROR loading RAG data: {e}")

    def lookup_policy(self, query: str) -> Dict[str, Any]:
        """
        [Function Calling Tool] Performs a similarity search on the policy database.
        """
        if self.collection.count() == 0:
            return {"status": "error", "message": "Policy knowledge base is not available."}
            
        results = self.collection.query(
            query_texts=[query],
            n_results=1
        )
        
        if results and results.get('documents') and results['documents'][0]:
            relevant_text = results['documents'][0][0]
            return {
                "status": "success",
                "relevant_policy": relevant_text,
                "message": "Policy information retrieved from Safar Travel knowledge base."
            }
        else:
            return {
                "status": "info",
                "message": "No direct match in the policy knowledge base."
            }

class DestinationTool:
    """This tool relies on the LLM's own knowledge for domestic travel suggestions."""

    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model
        
    def search_destinations(self, user_preferences: str) -> Dict[str, Any]:
        """
        [Function Calling Tool] Provides travel destination suggestions exclusively 
        for Iranian domestic cities based on user preferences.
        """
        
        prompt = f"""
        You are an expert Iranian travel agent. The user is looking for a domestic travel destination in Iran.
        
        User preferences: "{user_preferences}"
        
        Based on these preferences, provide a detailed, context-aware recommendation for 1 to 3 Iranian cities.
        
        Your output MUST be a JSON object with the following structure:
        {{
          "status": "success",
          "query": "{user_preferences}",
          "recommendations": [
            {{
              "city_fa": "نام شهر",
              "city_en": "City Name",
              "reasoning": "A brief reason why this city matches the user's preferences (e.g., 'historical sites', 'beach access', 'winter sports').",
              "attractions": ["Key attraction 1 (in Farsi and English)", "Key attraction 2 (in Farsi and English)"]
            }}
          ]
        }}
        
        Ensure all cities and recommendations are realistic and accurate for Iran. Do not include any text outside the JSON object.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_preferences} 
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            json_output = response.choices[0].message.content
            recommendations_data = json.loads(json_output)
            
            return {
                "status": "success",
                "message": "Destination suggestions generated by LLM reasoning. Use this data to present recommendations to the user.",
                "data": recommendations_data
            }

        except Exception as e:
            return {"status": "error", "message": f"Failed to generate destination recommendations using LLM reasoning: {str(e)}"}

def get_book_ticket_schema() -> Dict[str, Any]:
    return {
        "name": "book_ticket",
        "description": "Books a ticket in the simulated Safar Travel system. Required: Origin, Destination (Iran-only), Date, Name, National ID (کد ملی).",
        "parameters": {
            "type": "object",
            "properties": {
                "origin_city": {"type": "string", "description": "The city of departure (e.g., تهران, مشهد)."},
                "destination_city": {"type": "string", "description": "The destination city (e.g., کیش, شیراز)."},
                "travel_date": {"type": "string", "description": "The date of travel in YYYY-MM-DD format (Gregorian) or Persian date (e.g., 1403/05/10)."},
                "passenger_name": {"type": "string", "description": "The full name of the passenger."},
                "national_id": {"type": "string", "description": "The 10-digit Iranian National ID (کد ملی)."}
            },
            "required": ["origin_city", "destination_city", "travel_date", "passenger_name", "national_id"]
        }
    }

def get_cancel_ticket_schema() -> Dict[str, Any]:
    return {
        "name": "cancel_ticket",
        "description": "Cancels an existing ticket reservation using the ticket ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "The unique Safar Travel ticket ID (e.g., SF-TEKRQ-AB12C3)."},
            },
            "required": ["ticket_id"]
        }
    }

def get_ticket_info_schema() -> Dict[str, Any]:
    return {
        "name": "get_ticket_info",
        "description": "Retrieves detailed information about an existing ticket using the ticket ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "The unique Safar Travel ticket ID."},
            },
            "required": ["ticket_id"]
        }
    }

def get_lookup_policy_schema() -> Dict[str, Any]:
    return {
        "name": "lookup_policy",
        "description": "Performs a search on the policy database for company policies, FAQs, or rules.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The user's question or topic to search for (e.g., 'قوانین استرداد', 'حداکثر بار مجاز')."},
            },
            "required": ["query"]
        }
    }

def get_search_destinations_schema() -> Dict[str, Any]:
    return {
        "name": "search_destinations",
        "description": "Provides travel destination suggestions exclusively for Iranian domestic cities based on user preferences.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_preferences": {"type": "string", "description": "A description of what the user is looking for (e.g., 'یک شهر گرم با آثار تاریخی زیاد', 'مکانی برای اسکی')."},
            },
            "required": ["user_preferences"]
        }
    }



class SafarTools:
    """
    Aggregator class to hold and initialize all tools for the Agent Orchestration Layer.
    """
    def __init__(self, client: OpenAI, model: str):
        self.ticket_tool = TicketManagementTool()
        self.rag_tool = RAGTool()
        self.destination_tool = DestinationTool(client, model)

    def get_tool_callables(self) -> List[Any]:
        """
        Returns a list of actual Python functions (callables) for execution.
        Used by AgentManager._execute_tool_call
        """
        return [
            self.ticket_tool.book_ticket,
            self.ticket_tool.cancel_ticket,
            self.ticket_tool.get_ticket_info,
            self.rag_tool.lookup_policy,
            self.destination_tool.search_destinations,
        ]

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Returns a list of JSON-serializable tool schemas for the LLM API.
        Used by AgentManager.__init__ for self.openai_tools_specs
        """
        return [
            get_book_ticket_schema(),
            get_cancel_ticket_schema(),
            get_ticket_info_schema(),
            get_lookup_policy_schema(),
            get_search_destinations_schema(),
        ]