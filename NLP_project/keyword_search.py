import os
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import spacy
import re
from PyPDF2 import PdfReader
from docx import Document

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')

# Initialize NLP tools
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
nlp = spacy.load("en_core_web_sm")

def preprocess(text):
    """
    Preprocess the text by tokenizing, removing stop words, and lemmatizing.
    """
    # Use regular expressions to split text into words
    words = re.findall(r'\b\w+\b', text.lower())
    filtered_words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return filtered_words

def get_synonyms(keyword):
    """
    Get a set of synonyms for the given keyword using WordNet.
    """
    synonyms = set()
    for syn in wordnet.synsets(keyword):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return synonyms

def read_keywords(file_path):
    """
    Read keywords from a text file, each keyword on a new line.
    """
    keywords = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                keywords.add(line.strip())
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
    return keywords

def search_keywords_in_text(text, keywords):
    """
    Search for the given keywords in the preprocessed text and count their occurrences.
    """
    # results = {}
    # for keyword in keywords:
    #     if keyword in text:
    #         results[keyword] = text.count(keyword)
    # return results
    results = {}
    text_joined = ' '.join(text)
    for keyword in keywords:
        pattern = re.escape(keyword.lower())
        count = len(re.findall(r'\b' + pattern + r'\b', text_joined))
        if count > 0:
            results[keyword] = count
    return results

def extract_entities(text, names):
    """
    Extract named entities (NER) from the text using spaCy, filtering out only the entities that match the provided names.
    """
    entities = []
    doc = nlp(text)
    for ent in doc.ents:
        for name in names:
            name_parts = name.lower().split()
            ent_text_parts = ent.text.lower().split()
            if all(part in ent_text_parts for part in name_parts):
                entities.append((ent.text, ent.label_))
    return entities

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file using PyPDF2.
    """
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(docx_path):
    """
    Extract text from a DOCX file using python-docx.
    """
    text = ""
    try:
        doc = Document(docx_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text
    except Exception as e:
        print(f"Error reading DOCX file '{docx_path}': {e}")
    return text

def search_files_in_directory(directory, file_extension, keywords, names):
    matching_files = []
    all_keywords = set(keywords)
    
    for keyword in keywords:
        all_keywords.update(get_synonyms(keyword))
    
    for root, dirs, files in os.walk(directory):
        # Exclude unwanted directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', '__pycache__', '.git', 'nlpEnv']]
        for file in files:
            if file.endswith(file_extension) and not file.startswith("~$"):  # Check for the specified file extension and exclude temporary files
                file_path = os.path.join(root, file)
                if file_extension == ".pdf":
                    text = extract_text_from_pdf(file_path)
                elif file_extension == ".docx":
                    text = extract_text_from_docx(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                print(f"Reading file: {file_path}")  # Debug print
                preprocessed_text = preprocess(text)
                search_results = search_keywords_in_text(preprocessed_text, all_keywords)
                entities = extract_entities(text, names)
                if search_results or entities:
                    matching_files.append((file_path, search_results, entities))
    return matching_files

def display_results(matching_files, names):
    """
    Display the search results.
    """
    if not matching_files:
        print("\nNo results found.")
        return

    for file_path, results, entities in matching_files:
        print(f"\nFound File: {file_path}")
        if results:
            print("Keyword Occurrences:")
            for keyword, count in results.items():
                print(f"    {keyword}: {count}")
        if names and entities:
            print("Named Entities:")
            for entity, label in entities:
                print(f"    {entity}: {label}")
        print("")  # Add an empty line for better readability


if __name__ == "__main__":
           # Get user input for directory, file extension, keywords file path, and names
    directory = input("Enter the directory path: ")
    directory = directory.replace("\\", "\\\\")  # Format the directory path
    file_extension = input("Enter the file extension (e.g., .txt, .pdf, .docx): ")
    keywords_file_path = input("Enter the path to the keywords file (leave blank to enter keywords manually): ")
    names = input("Enter names separated by commas (leave blank if none): ").strip().split(',')

    # Clean up empty strings from the names list
    names = [name for name in names if name]

    if keywords_file_path:
        keywords = read_keywords(keywords_file_path)
    else:
        keywords = input("Enter keywords separated by commas (leave blank if none): ").strip().split(',')
        keywords = [kw for kw in keywords if kw]

    matching_files = search_files_in_directory(directory, file_extension, keywords, names)
    display_results(matching_files, names)
