import os
import requests
from dotenv import load_dotenv
import json
from datetime import datetime
import google.generativeai as genai
import time

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# Initialize Gemini client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')

# Check if API keys are loaded correctly
if not PERPLEXITY_API_KEY or not GEMINI_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY and GEMINI_API_KEY must be set in .env file")

# Define headers for the API request
headers = {
    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
    "Content-Type": "application/json"
}

# System prompt for the Perplexity API
system_prompt = """
You are an expert researcher tasked with compiling a comprehensive, clear, and concise summary of the specified person's philosophy, impact, and notable controversies/mistakes. Your goal is to:
1. Extract key principles, ideas, and insights from their public statements, writings, and interviews
2. Analyze their significant contributions to their field
3. Identify and explain their notable controversies, criticisms, or strategic mistakes (e.g., business decisions, public statements, or actions that were widely criticized or later proved problematic)

Focus on their views on technology, innovation, and society. Present the information in a structured format, including specific quotes where possible. If data is limited or unclear, note that and provide a reasonable interpretation based on available context.
"""

# List of people to analyze
people_to_analyze = [
    "Naval Ravikant", "Elon Musk", "Sam Altman", "Paul Graham", "Marc Andreessen",
    "David Sacks", "Donald Trump", "Andrej Karpathy", "Jeff Dean", "Ilya Sutskever",
    "Linus Torvalds", "Peter Thiel", "Vitalik Buterin", "Yuval Noah Harari",
    "Nick Bostrom", "Balaji Srinivasan", "Jaron Lanier", "Lex Fridman",
    "Yann LeCun", "Geoffrey Hinton", "Andrew Ng", "Yoshua Bengio", "Ray Kurzweil",
    "Alec Radford", "Tim Urban", "Eliezer Yudkowsky", "Max Tegmark", "George Hotz"
]

# Function to query Perplexity API
def query_perplexity(prompt):
    payload = {
        "model": "sonar",  # You can adjust the model as needed
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,  # Adjust based on desired response length
        "temperature": 0.7   # Balanced creativity and accuracy
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        print(f"Error querying Perplexity API: {e}")
        return None

def query_gemini(text):
    try:
        prompt = f"""Convert this text into hierarchical bullet points using markdown hyphens (-), removing any hashtags and unnecessary denotations. 
        Format it like this:
        - Main point
          - Subpoint
            - Sub-subpoint
        
        Here's the text to convert: {text}"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error querying Gemini API: {e}")
        return None

# Function to save results to a file
def save_to_file(content, filename, mode="w"):
    timestamp = datetime.now().strftime("%Y%m%d")
    output_filename = f"thought_leaders_{timestamp}.md"
    
    # Process content through Gemini for bullet point formatting
    formatted_content = query_gemini(content)
    
    with open(output_filename, mode, encoding="utf-8") as f:
        f.write(f"\n\n## {filename}\n")
        f.write(formatted_content if formatted_content else content)
    print(f"Results appended to {output_filename}")

# Function to read names from a file
def read_names_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # Strip whitespace and empty lines
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return []

# Function to check if person has already been analyzed
def is_already_analyzed(person, output_file):
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for section headers with the person's name
            return f"## {person}" in content
    except FileNotFoundError:
        return False

# Main function to scrape philosophies
def scrape_philosophies():
    # Read names from all files
    contemporary_names = read_names_from_file('contemporary.txt')
    classical_new_names = read_names_from_file('classical_new.txt')
    classical_old_names = read_names_from_file('classical_old.txt')
    
    # Combine all names
    all_names = contemporary_names + classical_new_names + classical_old_names
    
    # Get timestamp for output file
    timestamp = datetime.now().strftime("%Y%m%d")
    output_filename = f"thought_leaders_{timestamp}.md"
    
    for person in all_names:
        # Skip if person has already been analyzed
        if is_already_analyzed(person, output_filename):
            print(f"Skipping {person} - already analyzed")
            continue
            
        print(f"\nAnalyzing {person}...")
        prompt = f"""Provide a detailed analysis of {person}, including:
1. Their key philosophical ideas and principles
2. Major contributions and impact in their field
3. Notable controversies, criticisms, or strategic mistakes they've made
4. How these mistakes or controversies have affected their work or reputation"""

        result = query_perplexity(prompt)
        
        if result:
            print(f"=== {person}'s Philosophy ===")
            print(result)
            # For the first unanalyzed person, use "w" mode if file doesn't exist
            mode = "a" if os.path.exists(output_filename) else "w"
            save_to_file(result, person, mode)
        else:
            print(f"Failed to retrieve information about {person} from Perplexity API.")
        
        # Add a small delay to avoid rate limiting
        time.sleep(2)

# Run the script
if __name__ == "__main__":
    scrape_philosophies()