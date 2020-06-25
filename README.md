# ContRanker

## Project Description:

Contranker helps a startup called Homestead in ranking General contractors and find suitable new contractors for their future projects.
Homestead specifically transforms underutilized assets—garages, empty rooms, backyards—into rental apartments (formally called ADUs). They want to build more ADU projects in the future to 
help homeowners make money and more importantly, solve California’s housing crisis: which was a shortage of ~3 million housing units (as of 2018).
Homestead needs general contractors, BUT Very few contractors have built an ADU so far. So the ultimate goal is Predicting ADU construction performance of contractors who have never built an ADU and ranking them accordingly. To solve this problem, I scraped and preprocessed
1. Data of contractors licenses, previous projects and reviews 
2. Based on expertise knowledge, For those contractors who have done ADU before We can evaluate their ADU performance and label the data.
3. So the problem is looking at ADU-builders and learning correlations between historical non-ADU performance of contractors and their ADU performance. Then, we can use the learned model to predict ADU performance of contractors who have never built an ADU.

The challenge was that there was no structured labeled dataset for this problem. So I scraped and preprocessed public permits and inspections and found licensed contractors who have built ADUs before. 
By combining construction time and inspections with a weighted Average of completed ADUs I labeled adu-builders with ADU performance score.

I did feature engineering and found some non-ADU important features such as 
Avg time per inspection and yearly completed number of projects.

I also looked at some general characteristics of contractors. I considered Time since first completed project as a measure of experience. I scraped buildzoom website and added average rating and # of reviews to features.
Then based on non-ADU features of adu-builders as input and their ADU performance score as output, I trained a Random forest regressor model with 100 trees. 
I used Random Forest Regressor since It can handle nonlinearities, is less prone to overfitting with small training dataset and has higher interpretability compared to more complex models. As you can see on the right side, after training, we have feature importances with Average Time per Inspection being the most important feature.
I limited the depth of random forest model to 7 to avoid overfiting. I also eliminated outliers which resulted in a more accurate predictive model.
With the trained model, I predicted ADU performance scores and provided a Ranked list of contractors who have built less than 2 ADUs for future Homestead ADU projects.

[Slides link](https://docs.google.com/presentation/d/1R4nccibpYNh5gY2cqWeEwZOTNMzhZImFTqilqU__gO4/edit#slide=id.g89a8987e0f_0_16)
[Public LA Permits dataset](https://data.lacity.org/A-Prosperous-City/Building-and-Safety-Permit-Information-Old/yv23-pmwf)
[Public LA inspections dataset](https://data.lacity.org/A-Safe-City/Building-and-Safety-Inspections/9w5z-rg2h)
