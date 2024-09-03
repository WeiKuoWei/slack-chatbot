import re
import asyncio
import nltk
import spacy
import json
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from concurrent.futures import ThreadPoolExecutor
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

class TextProcessor:
    def __init__(self):
        # Load spaCy language model
        self.nlp = spacy.load("en_core_web_sm")
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

    # --------- Preprocessing Functions --------- #
    def preprocess_text(self, text):
        # Tokenization
        tokens = word_tokenize(text)

        # Remove Noise
        cleaned_tokens = [re.sub(r'[^\w\s]', '', token) for token in tokens]

        # Remove empty strings
        cleaned_tokens = [token for token in cleaned_tokens if token]

        # Other preprocessing steps
        cleaned_tokens = [token.lower() for token in cleaned_tokens]
        cleaned_tokens = [token for token in cleaned_tokens if token not in self.stop_words]
        cleaned_tokens = [self.lemmatizer.lemmatize(token) for token in cleaned_tokens]

        return cleaned_tokens

    async def async_preprocess_text(self, text):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            result = await loop.run_in_executor(pool, self.preprocess_text, text)
        
        result = [token for token in result if 3 <= len(token) <= 20]
        cleaned_text = ' '.join(result)
        return cleaned_text

    async def preprocess_documents(self, documents):
        cleaned_documents = []
        for doc in documents:
            cleaned_doc = await self.async_preprocess_text(doc)
            cleaned_documents.append(cleaned_doc)
        return cleaned_documents

    # ---------- Extracting Metadata ---------- #
    def extract_metadata(self, text):
        doc = self.nlp(text)
        meta_data = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
        
        # Filter out undesired labels
        filtered_meta_data = [
            meta for meta in meta_data 
            if meta['label'] not in ["CARDINAL", "DATE", "TIME", "QUANTITY"]
        ]
        
        if not filtered_meta_data:  # Check if filtered metadata is empty
            return None
        
        meta_data_json = json.dumps(filtered_meta_data)
        print(f"Metadata: {meta_data_json}")
        
        return meta_data_json

    async def async_extract_metadata(self, text):
        return await asyncio.to_thread(self.extract_metadata, text)

    # ---------- Extracting Keywords ---------- #
    def extract_keywords(self, documents, top_n=10):
        vectorizer = TfidfVectorizer(max_df=0.85, stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.sum(axis=0).A1
        tfidf_scores = zip(feature_names, tfidf_scores)
        sorted_scores = sorted(tfidf_scores, key=lambda x: x[1], reverse=True)
        keywords = [word for word, score in sorted_scores[:top_n]]
        return keywords

    async def async_extract_keywords(self, documents, top_n=10):
        return await asyncio.to_thread(self.extract_keywords, documents, top_n)

    # ---------- Extracting Key Phrases ---------- #
    def extract_key_phrases(self, text):
        doc = self.nlp(text)
        key_phrases = [
            chunk.text for chunk in doc.noun_chunks 
            if 3 <= len(chunk.text) <= 20
        ]
        key_phrases = [phrase for phrase in key_phrases if len(phrase) >= 1]
        return key_phrases

    async def async_extract_key_phrases(self, text):
        return await asyncio.to_thread(self.extract_key_phrases, text)
        
    # ---------- Processing Messages ---------- #
    async def process_messages(self, contents):
        # Preprocess the messages
        cleaned_documents = await self.preprocess_documents(contents)

        # Extract key phrases
        key_phrases_tasks = [self.async_extract_key_phrases(doc) for doc in contents]
        key_phrases = await asyncio.gather(*key_phrases_tasks)
        key_phrases = [phrases for phrases in key_phrases if phrases]

        # Extract metadata
        metadata_tasks = [self.async_extract_metadata(doc) for doc in contents]
        metadata = await asyncio.gather(*metadata_tasks)
        metadata = [meta for meta in metadata if meta]

        # Extract keywords
        keywords = await self.async_extract_keywords(cleaned_documents)

        return cleaned_documents, key_phrases, metadata, keywords


# # Example usage
# if __name__ == "__main__":
#     documents = ['bot removed channel type invite add bot back', 'doctorpatient channel interaction two user weiiiiiii_ therealjeffbezos user weiiiiiii_ initiated conversation greeting doctor asking permission enter conversation doctor proceeded inquire user symptom focusing stomach pain dizziness user mentioned experiencing stomach ache dizziness day examination doctor determined user likely stomach infection food poisoning doctor asked user recent diet user mentioned consuming food stall fair could led food poisoning due unhygienic condition based symptom information provided doctor provided diagnosis advised user accordingly conversation also included user expressing gratitude confirming location pain stomach additionally multiple instance user weiiiiiii_ repeatedly asked c going channel indicating query ongoing activity discussion channel', 'c going channel', 'source boom construction competition http manualegpolyeduindexphpboom_construction_competition', 'boom construction competition lab activity team design assemble boom lift heavy object competition judge boom based factor like mass length anchor time mass support without deflecting rule include anchoring boom within 2 minute specific dimension boom extension starting height limitation cutting dowel material behavior load aging must considered design improvement optimize boom performance competition encourages critical thinking material selection loadbearing capacity structural integrity handson way student apply engineering principle practical setting', 'g tell u boom construction competition', 'source boom construction competition http manualegpolyeduindexphpboom_construction_competition', 'boom construction competition lab 7 specific rule must adhered order qualify competition key rule need follow 1 boom must anchored white plastic anchorage provided 2 dowel must used asis cut 3 boom must extend least 15 meter horizontally front edge anchorage 4 boom must start least 030 meter ground adding 15 gram preload 5 boom must anchored 2 minute le 6 boom may touch anything anchorage 7 boom performance assessed based anchor time boom mass boom length mass support deflecting 020 meter vertically 8 team use number dowel long total length le equal length 4 uncut dowel following rule ensure boom design eligible competition', 'g currently working lab 7 competing boom construction competition competition rule follow', 'doctorpatient channel interaction user weiiiiiii_ doctor user initially greeted doctor asked permission enter conversation doctor inquired user symptom specifically focusing stomach pain dizziness user mentioned experiencing stomach ache dizziness day examination doctor determined user likely stomach infection food poisoning doctor asked user recent diet user mentioned consuming food stall fair could led food poisoning due unhygienic condition based symptom information provided doctor provided diagnosis advised user accordingly conversation also included user expressing gratitude confirming location pain stomach additionally separate query user weiiiiiii_ boom construction competition asked information another user leeden mentioned working lab 7 participating boom construction competition inquiring competition rule follow', 'c going channel', 'source boom construction competition http manualegpolyeduindexphpboom_construction_competition', 'boom construction competition lab activity team design assemble boom lift heavy object competition judge boom based factor like boom mass length anchor time mass support without deflecting rule include anchoring boom within 2 minute specific dimension restriction cutting dowel material behavior load aging must considered design improvement optimize boom performance load direction stress boom crucial deviation rule lead disqualification overall competition challenge student apply engineering principle create efficient effective boom', 'g tell u boom construction competition', 'source boom construction competition http manualegpolyeduindexphpboom_construction_competition', 'boom construction competition lab 7 specific rule must followed qualify competition rule include anchoring boom white plastic anchorage provided using dowel without cutting ensuring boom extends least 15m horizontally anchorage starting boom least 030m ground adding 15 gram preload anchoring boom 2 minute le ensuring boom touch anything anchorage assessing boom performance based anchor time boom mass boom length mass support deflecting 020m vertically additionally team use number dowel long total length le equal length 4 uncut dowel rule crucial follow avoid disqualification ensure fair competition', 'g currently working lab 7 competing boom construction competition competition rule follow', 'doctorpatient channel user weiiiiiii_ interacting doctor user initially greeted doctor asked permission enter conversation doctor proceeded ask user symptom specifically focusing stomach pain dizziness user mentioned experiencing stomach ache dizziness day upon examination doctor determined user likely stomach infection food poisoning doctor inquired user recent diet user mentioned consuming food stall fair could led food poisoning due unhygienic condition doctor provided diagnosis advised user accordingly', 'c going channel', 'going channel', 'okay doctor thank', 'good prescribing medicine one week come back checkup next week please try avoid spicy fried food', 'think never eat unhygienic place future', 'okay probably suffering food poisoning since food stall fair quite unhygienic high chance uncovered food might caused food poisoning', 'actually went fair last week ate food stall', 'well suffering stomach infection reason stomach ache also getting dizzy change diet recently something unhealthy', 'yes doctor pain sharpest', 'okay let check applies pressure stomach check pain hurt', 'yes doctor feeling well past day stomach ache day feeling bit dizzy since yesterday', 'good morning look quite pale morning', 'good morning doctor may come']

#     processor = TextProcessor()
#     cleaned_documents, key_phrases, metadata, keywords = asyncio.run(processor.process_messages(documents))

#     # Example print statements for debugging (can be uncommented)
#     # print("Cleaned documents:", cleaned_documents)
#     print("Key phrases:", key_phrases)
#     print("Metadata:", metadata)
#     print("Keywords:", keywords)
