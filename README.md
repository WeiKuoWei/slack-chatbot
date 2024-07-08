# Slack Chatbot 
## Project Description
[Repository Update: 2024-07-03]
It is decided that the Chatbot should be installed on both Slack and Discord. Thus, a more general approach is needed to make the Chatbot work on both platforms. Message extracting files for Slack and Discord will be created from the old `messageExtractor.py`, and the original file will be replaced with `getMessageSlack.py` and `getMessageDiscord.py`. `modelsChroma.py` will be deleted, while other `.py` files will be updated to work with the new message extracting files. 

