import pandas as pd
import numpy as np
import statistics
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error


def train_model(adu_builder_data):
    '''
    predicts ADU performance score (inefficiency score: less score is better) from general non-ADU features
    :param data: learning data from users with at least two complete ADU projects, non-ADU general input features
    and ADU-related performance
    :return:
    '''

    data = adu_builder_data[['Bldg-New_count', 'Bldg-Alter/Repair_count', 'Bldg-Addition_count','avg_construction_time',
       '2020_proj_count', '2019_proj_count', '2018_proj_count',
       '2017_proj_count', '2016_proj_count', '2015_proj_count', '2020_avg_numb_insp' ,'2019_avg_numb_insp',
                                          '2018_avg_numb_insp' ,'2017_avg_numb_insp','2016_avg_numb_insp' ,'2015_avg_numb_insp',
'2014_avg_numb_insp' ,'2013_avg_numb_insp',
       '2014_proj_count', '2013_proj_count','experience',
       'non_ADU_proj_count', 'non_ADU_avg_insp','w_avg_time_per_insp','ADU_performance_score']]

    y = data['ADU_performance_score']
    x = data.drop('ADU_performance_score', axis=1)
    max_depths = [7]
    #max_depths = [3,5,6,7,9,11]
    min_samples_splits = [10]
    #min_samples_splits = [6,8,10,12]
    n_estimators = [100]
    #n_estimators = [10,100]
    max_rmse = -10
    max_rmse_params = []
    max_map = 0
    max_map_params = []
    for max_depth in max_depths:
        for min_samp in min_samples_splits:
            for n_est in n_estimators:
                print('max_depth: '+str(max_depth)+ ", min_sample_split: "+str(min_samp)+", numb_estim: "+str(n_est))
                results = []
                exp_res = []
                comp_res = []
                time_res = []
                pred_rmses = []
                actual_rmses = []
                train_rmses = []
                for i in range(0, 100):

                    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.20)
                    print("learning from")
                    print(x_train.shape)
                    print("testing on")
                    print(x_test.shape)
                    RFRegressor = RandomForestRegressor(n_estimators= n_est, max_depth = max_depth)
                    #RFRegressor = RandomForestRegressor(n_estimators= n_est)

                    RFRegressor.fit(x_train,y_train)

                    y_pred = RFRegressor.predict(x_test)
                    y_train_pred = RFRegressor.predict(x_train)
                    output = pd.DataFrame({'index': y_test.index.to_list(), 'prediction': y_pred, 'actual': y_test})
                    pred_ranking = output.sort_values(['prediction'])['index']
                    actual_ranking = output.sort_values(['actual'])['index'][:10]

                    cv_score = _ap(actual_ranking, pred_ranking.to_list(), k=10)
                    results.append(cv_score)

                    base_data = adu_builder_data[['experience', 'non_ADU_proj_count','avg_construction_time']]
                    base_data['index'] = base_data.index.to_list()
                    output = output.merge(base_data, on='index', how='inner')
                    exp_ranking = output.sort_values(['experience'], ascending=False)['index'][:10]
                    comp_ranking = output.sort_values(['non_ADU_proj_count'], ascending=False)['index'][:10]
                    random_ranking = output.sample(frac=1)['index']
                    time_ranking = output.sort_values(['avg_construction_time'], ascending=False)['index'][:10]

                    exp_res.append(_ap(actual_ranking, exp_ranking.to_list(), k=10))
                    comp_res.append(_ap(actual_ranking, comp_ranking.to_list(), k=10))
                    time_res.append(_ap(actual_ranking, time_ranking.to_list(), k=10))

                    pred_mse = mean_squared_error(y_test, y_pred)
                    pred_rmse = np.sqrt(pred_mse)
                    y_mean = [statistics.mean(y_train)] * len(y_pred)
                    actual_mse = mean_squared_error(y_test, y_mean)
                    train_mse = mean_squared_error(y_train, y_train_pred)
                    train_rmse = np.sqrt(train_mse)
                    actual_rmse = np.sqrt(actual_mse)
                    pred_rmses.append(pred_rmse)
                    actual_rmses.append(actual_rmse)
                    train_rmses.append(train_rmse)

                    feats = pd.Series(RFRegressor.feature_importances_, index=x_train.columns)
                    feats = feats.sort_values()
                if statistics.mean(results) > max_map:
                    max_map = statistics.mean(results)
                    max_map_params = [max_depth, min_samp, n_est]
                    max_model = RFRegressor


                if statistics.mean(actual_rmses) - statistics.mean(pred_rmses) > max_rmse:
                    max_rmse = statistics.mean(actual_rmses) - statistics.mean(pred_rmses)
                    max_rmse_params = [max_depth, min_samp, n_est]

                print(feats)

    print(statistics.mean(results))
    print(statistics.mean(time_res))
    print(max_map)
    print(max_map_params)

    return max_model


def predict_adu_performance_non_ADU_builders(model, non_adu_builders):
    """
    predict ADU performance for builders with <=2 ADU projects based on the trained model
    :param model: trained model on ADU-builders data
    :param non_adu_builders: builders with <=2 ADU projects for whom we want to predict the ADU performance score
    :return: ranked list of contractors by their predicted ADU performance
    """
    non_ADU_builder_features = non_adu_builders[['Bldg-New_count', 'Bldg-Alter/Repair_count', 'Bldg-Addition_count',
                      '2020_proj_count', '2019_proj_count', '2018_proj_count',
                      '2017_proj_count', '2016_proj_count', '2015_proj_count',
                      '2014_proj_count', '2013_proj_count', '2020_avg_numb_insp', '2019_avg_numb_insp',
                      '2018_avg_numb_insp', '2017_avg_numb_insp', '2016_avg_numb_insp', '2015_avg_numb_insp',
                      '2014_avg_numb_insp', '2013_avg_numb_insp', 'experience',
                      'non_ADU_proj_count', 'non_ADU_avg_insp', 'w_avg_time_per_insp','avg_construction_time']]
    y_pred = model.predict(non_ADU_builder_features)
    output = pd.DataFrame({'index': non_ADU_builder_features.index.to_list(), 'adu_performance_prediction': y_pred})

    non_adu_builders['index'] = non_adu_builders.index.to_list()
    output = output.merge(non_adu_builders, on='index', how='inner')
    output = output.sort_values(['adu_performance_prediction'])
    #output = output.drop(['ADU_performance_score'])
    return  output


def _ap(actual, predicted, k=10):
    """
    Computes the average precision at k.
    Parameters
    ----------
    actual : list
        A list of actual items to be predicted
    predicted : list
        An ordered list of predicted items
    k : int, default = 10
        Number of predictions to consider
    Returns:
    -------
    score : int
        The average recall at k.
    """
    if len(predicted)>k:
        predicted = predicted[:k]

    score = 0.0
    num_hits = 0.0

    for i,p in enumerate(predicted):
        if p in actual and p not in predicted[:i]:
            num_hits += 1.0
            score += num_hits/(i+1)

    return score / k

