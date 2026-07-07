# Learnings

## Project Structure
I learned how does a production grade project structure look like. So I made copied this project structure from LinkedIn and made some changed according to my personal choice. 

## Data Simulation
- I simulated the data as you can see like a actual companies data department will give me from a MongoDB database or something like that.
- ChromaDB doesnt store lists in the metadata so we wont be able to use the where clause properly instead we will use the $contains thing in the where clause. For other handling json loads and json dumps is enough.

## Error Handling
- Enclose all sections in proper try except blocks even nested if required
- Instead of using print functions use logger functions like logger.error and logger.info

## Embedding Making
- First I decided between FAISS and ChromaDB because I needed heavy metadata filtering so I chose ChromaDB
- After that for chromaDB I learnt that using langchain's Chroma we dont get much control so we will use the dedicated chromdb library for it.
- Then to write a generalized professional clean function for embedding I needed to write a data preprocesssing function that unified the data from the data department and sort them into generalized fields like content metadata and ids.
- Also production ready codes keep in mind that there will be a time after development when there wont be mocked data there will be mocked real data so one shoul dprefer batch operations if some library supports as they are optimized for that.


## Batching
- My doubt came when I was writing the agent 1 of layer 1 was that shouldn't I use batch instead of invoke then I got to know that is the job at the infrastrcuture level and in production will be handled by uvicorn + fastapi

## Internals
- The functions or variables which are only for the use internally shoul dstart with _ and also if they need to be static instantiate then dont put them inside the functions which will trigger unwanted resinstantiations.