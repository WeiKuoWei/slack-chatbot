# Project Management Chatbot on Discord

## Overview

This project, developed under NYU Tandon's Flexible AI-enabled Mechatronic Systems Lab (FAMS), is a sophisticated application that integrates generative AI to enhance project management for both teachers and students. Designed to operate on Discord, the chatbot captures user requests and interactions, leveraging advanced microservices and interfaces to improve collaboration and efficiency in educational environments. Users can ask questions related to their channels or course materials and receive accurate, context-aware responses.

## Key Features

- **Hierarchical Expert System:** Employs a two-tier semantic routing architecture to direct queries to 8 specialized experts (5 course-related, 3 health-related).
- **Automatic Centroid Vector Routing:** Calculates and updates centroid vectors from document embeddings, eliminating the need for manual utterances.
- **Group Chat & Context Awareness:** Supports multiple simultaneous users with conversation history to maintain context across interactions.
- **User Profiles:** Creates personalized profiles to deliver customized responses based on individual needs and preferences.
- **Sentiment & Profanity Analysis:** Automatically flags and reports offensive content to professors, ensuring a safe and productive environment.
- **Secure & Scalable Deployment:** Deployed on Kubernetes with SSO authentication, ensuring secure access and robust performance.

## Architecture

![Chatbot Architecture](./images/poster.png)

### Semantic Router Architecture

The system uses a hierarchical semantic router that:
1. Calculates centroid vector representations of document collections for each expert
2. Groups experts into broader categories (course and health)
3. Routes queries first to the appropriate group, then to the specific expert
4. Automatically updates centroids when new documents are added

## Prerequisites

- **Discord Bot Setup:** Create and configure a bot on Discord with the necessary permissions.
- **Dependencies:** Ensure all required Python packages are installed.
- **OpenAI API Key:** A functional OpenAI key is necessary for AI functionalities.
- **Vector Database:** ChromaDB with SQLite for storing embeddings and document collections.

## Installation

1. **Clone the Repository:**
   ```sh
   git clone https://github.com/your-repository-url.git
   cd your-repository
   ```

2. **Install Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set Up the Discord Bot:**
   - Follow Discord's guide to create a bot and obtain a token.
   - Configure the necessary permissions for the bot.

4. **Configure Environment Variables:**
   - Add your OpenAI API key and other environment-specific variables to a `.env` file.

5. **Run the Program:**
   ```sh
   python src/main.py
   ```

## Usage

Once set up, the bot will automatically start listening to channels it's invited to and provide the following functionalities:

- **Central Broker Access:** Interact with the main broker chatbot which directs queries to appropriate experts.
- **Expert-Specific Queries:** Access specialized knowledge across academic and wellness domains.
- **Document Upload:** Add personal documents to get customized assistance.
- **Group Discussions:** Collaborate with peers while maintaining contextual awareness.
- **Progress Tracking:** Monitor project milestones and receive personalized productivity tips.
- **Generate Educational Analytics:** Professors receive insights on student engagement, team collaboration dynamics, and project progress.

## Adding New Experts

To add a new expert to the system:
1. Collect relevant documents for the expert's domain
2. Upload documents using the provided interface
3. The system automatically generates centroid vectors and updates group centroids
4. Configure the expert's response handling as needed

## Contributing

We welcome contributions to enhance the bot's capabilities. Please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
```
