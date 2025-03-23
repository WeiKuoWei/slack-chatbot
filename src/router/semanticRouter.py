from semantic_router import Route, RouteLayer
from semantic_router.encoders import OpenAIEncoder
import os, sys, logging, inspect 

# Adding path to ensure utils and backend are detected
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utlis.config import OPENAI_API_KEY
from utlis.prompts import PROMPTS
from backend.modelsPydantic import QueryRequest
from database.modelsChroma import generate_embedding
from services.queryLangchain import fetchGptResponse
from services.queryLangchain import generateGeminiRespone
from router.utterances import UTTERANCES
from google.genai.types import GenerateContentConfig

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

config = GenerateContentConfig(
    system_instruction=PROMPTS['reroute_expert']
)

class SemanticRouter:
    def __init__(self, crud):
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Set up variables
        self.crud = crud
        self.encoder = OpenAIEncoder()
        self._setup_routes()
        
    def _setup_routes(self):
        """Initialize routes and route layer"""
        # Route definitions and their utterances
        self.progress_report_rt = Route(
            name="progress_report",
            utterances=UTTERANCES["progress_report"],
        )

        self.problem_solve_rt = Route(
            name="problem_solve",
            utterances=UTTERANCES["problem_solve"],
        )

        self.material_info_rt = Route(
            name="material_info",
            utterances=UTTERANCES["material_info"],
        )

        self.mental_support_rt = Route(
            name="mental_support",
            utterances=UTTERANCES["mental_support"],
        )

        # Define Route Layer
        self.route_layer = RouteLayer(encoder=self.encoder, routes=[
            self.progress_report_rt,
            self.problem_solve_rt,
            self.material_info_rt,
            self.mental_support_rt,
        ])
        
        # Setup response mapping
        self.route_responses = {
            "progress_report": self.progress_report_guidance,
            "problem_solve": self.problem_solve_guidance,
            "material_info": self.material_info_guidance,
            "mental_support": self.mental_support_guidance,
            "fallback": self.fallback_response,
        }
    
    # Response functions
    async def progress_report_guidance(self, route, request=None):
        return "Tracking your submitted labs and reviewing feedback will help ensure steady progress."

    async def problem_solve_guidance(self, route, request=None):
        return "Start by breaking the problem into smaller parts and focus on the key concepts."

    async def material_info_guidance(self, route, request):
        return await self.generate_expert_response(route, request, collection_name="course_materials", prompt_name="course_instructor")

    async def mental_support_guidance(self, route, request=None):
        return "If you are feeling overwhelmed, NYU provides free counseling services to help students manage stress."

    async def fallback_response(self, request=None):
        return "I'm not sure I understood that. Could you rephrase or ask something more specific?"
        
    async def generate_expert_response(self, route, request: QueryRequest, collection_name, prompt_name):
        """Generates response using LLM and relevant documents"""

        if request.has_been_rerouted == False:
            user_query =f"Query: {request.query}, Chosen Route: {route}"
            reroute_assessment = await generateGeminiRespone(user_query,config)
            if reroute_assessment.find('No') != -1:
                revised_query_index = reroute_assessment.find("Revised Query: ")
                if revised_query_index != -1:
                    revised_query = reroute_assessment[revised_query_index+15:]
                    #revised query to be passed back into semantic router
                    request.has_been_rerouted = True
                    request.query = revised_query
                    await self.process_query(request)
        
        query_embedding = await generate_embedding(request.query)
        collection_name = collection_name
        relevant_docs = await self.crud.get_data_by_similarity(collection_name, query_embedding, top_k=5)
        
        content = relevant_docs.get('documents')[0]
        logging.info(f"Relevant messages: {content}")

        answer = await fetchGptResponse(request.query, PROMPTS[prompt_name], relevant_docs)

        # rerouting checker is here, where we'll set the variable and see if it needs context or not
        #should we potetially set the query variable to true just as a sign that its been check or no?
        # need to make sure we pass in the reshaped query

        logging.info(f"Answer: {answer}")
        return {'answer': answer}

    async def process_query(self, request: QueryRequest):
        """Main entry point to process a query through the semantic router"""
        try:
            route = self.route_layer(request.query)
            

            # Log the processed route details
            logging.info(f"Processed route: {route}")

            if hasattr(route, 'name') and route.name:
                print(route.name)
                response_function = self.route_responses.get(route.name, self.fallback_response)

                # Handle async and non-async functions
                if inspect.iscoroutinefunction(response_function):
                    response = await response_function(route.name, request)
                else:
                    response = response_function(route.name, request)
            else:
                response = await self.fallback_response(request)

            # Ensure response is properly formatted
            if inspect.iscoroutine(response):
                response = await response 
                
            if isinstance(response, dict):
                return response  
            elif isinstance(response, str):
                return {"answer": response}  
            else:
                return {"answer": str(response)} 

        except Exception as e:
            logging.error(f"Error processing query: {request.query} | Error: {e}")
            return {"error": str(e)} 

# Factory function to create router instance
def create_router(crud):
    return SemanticRouter(crud)