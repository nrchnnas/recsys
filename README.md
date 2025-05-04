# [AIC-601] Book Recommender System 📚
## required libraries to install before deployment 
### for server and recommender system
1. download `books.db` at [this link](https://drive.google.com/file/d/1TKkd19sg1nJm3Cgyfc3V0vH4Cj_MY3sD/view?usp=sharing) and add it into 'recsys' directory
2. in `recsys` directory, run `pip install -r requirements.txt`

### for website 
1. install [node.js](https://nodejs.org)
2. ensure that you installed node.js correctly by executing `node -v` and `npm -v` in terminal 

## how to deploy project
### deploy server
1. open your terminal
2. make sure your directory is `recsys`
3. run `python sever.py`
### deploy website 
*note: deploy server first*
1. open your terminal
2. make sure your directory is `recsys/book-rec-sys`
3. if you're running for the first time, run `npm install`
4. otherwise, run `npm run dev`
   
## other things of note
### how to run eda.ipynb
1. download `books.db` at [this link](https://drive.google.com/file/d/1TKkd19sg1nJm3Cgyfc3V0vH4Cj_MY3sD/view?usp=sharing)
2. make sure that root directory is `recsys`
3. create new folder called `data`
4. add `books.db` into `data` folder
5. execute each cell or run all in `eda.ipynb`

### how to run recommender_evaluation.py
1. download `filtered_interactions.csv` at [this link](https://drive.google.com/file/d/1KB0e3Iiz3UW9NoSUpSZNZhrIS6ZvJOkj/view?usp=sharing)
2. make sure 'filtered_interactions.csv is in the same directory as recommender_evaluation
3. run 'python recommender_evaluation.py' 
