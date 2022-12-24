import time
import xlsxwriter
from os import system
from scipy.stats import beta
from math import floor
import numpy as np
import pandas as pd
from math import sqrt, log

def get_norm(value, score_max, score_min):
    return value-score_min/score_max-score_min


def get_min_sample(conInt=0, pop=0, zVal=1.96):
    if conInt == 0:
        return None
    if pop == 0:
        ss = ((zVal * zVal) * 0.25) / ((conInt / 100) * (conInt / 100))
    else:
        ss = ((zVal * zVal) * 0.25) / ((conInt / 100) * (conInt / 100))
        ss = ss/(1+(ss-1)/pop)
    return int(ss+.5)


def score_beta(score_avg, votes, rating_prior, votes_prior, score_max=0, score_min=0):
    # https://medium.com/airy-science/search-ranking-with-bayesian-inference-608275e36ee
    norm = get_norm(score_avg, score_max, score_min) if score_max else score_avg
    norm0 = get_norm(rating_prior, score_max, score_min) if score_max else rating_prior
    success = norm * votes
    failure = votes - success
    prior_alpha = norm0 * votes_prior
    prior_beta = votes_prior - prior_alpha
    dist_alpha = prior_alpha + success
    dist_beta = prior_beta + failure
    beta_dist = beta(dist_alpha, dist_beta)
    # get the lower_beta from probability density function where x < lower_beta
    # contains 0.05 area of distribution and 0.95 area for x > lower_beta
    lower_beta = beta_dist.ppf(0.05)
    return lower_beta


def score_j2kun(ratings, rating_prior, rating_utility):
    # https://jeremykun.com/2017/03/13/bayesian-ranking-for-rated-items/
    '''
    score: [int], [int], [float] -> float

    Return the expected value of the rating for an item with 
    known ratings specified by `ratings`, 

    prior belief specified by `rating_prior`, and

    a utility function specified by `rating_utility`,

    assuming the ratings are a multinomial distribution and

    the prior belief is a Dirichlet distribution.
    '''
    ratings = [r + p for (r, p) in zip(ratings, rating_prior)]
    score = sum(r * u for (r, u) in zip(ratings, rating_utility))
    return score / sum(ratings)


def score_imdb(score_avg, votes, rating_prior, votes_prior, score_max=0, score_min=0):
    # https://help.imdb.com/article/imdb/track-movies-tv/ratings-faq/G67Y87TFYYP6TWAV
    rating = get_norm(score_avg, score_max,
                      score_min) if score_max else score_avg
    rating_prior = get_norm(rating_prior, score_max,
                            score_min) if score_max else rating_prior
    return rating*votes/(votes+votes_prior)+rating_prior*votes_prior/(votes+votes_prior)


def score_wilson(score_avg, votes, weight = 1.959964, score_max=0, score_min=0):
    # https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval
    rating = get_norm(score_avg, score_max, score_min) if score_max else score_avg
    return ((rating + (weight * weight) / (2 * votes)) - (weight / (2 * votes)) * sqrt(4 * votes * rating * (1 - rating) + (weight * weight))) / (1 + (weight * weight) / votes)


def score_log(score_avg, votes, votes_max, score_max=0, score_min=0):
    rating = get_norm(score_avg, score_max, score_min) if score_max else score_avg
    return rating*log(votes, votes_max)


def getn(n0, n1, n2, n3, ratio):
    if n0 < ratio or n1 < ratio or n2 < ratio or n3 < ratio:
        return 100-floor(n1*100)

def rank(file_path: str, sheet_name=0, save_path: str = 'ranked.xlsx', score_col: str = 'score', votes_col: str = 'votes', min_votes=3, ratio=0.1, sort_type: str = 'simple'):
    ext = file_path.split('.')[-1]
    df: pd.DataFrame = None
    if ext == 'xlsx':
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    elif ext == 'csv' or ext == 'txt':
        df = pd.read_csv(file_path)
    df = df.query(f'{score_col} > 0 & {votes_col} >= @min_votes').astype({score_col: float, votes_col: int})
    sa = df[score_col].values
    va = df[votes_col].values
    score_max = sa.max()
    score_min = sa.min()
    nsa = (sa-score_min)/(score_max-score_min)
    rating_prior = np.median(nsa)
    votes_base = max(np.median(va), np.average(va))
    k = floor(va.size*ratio)
    votes_prior = np.partition(va, -k)[-k]
    df['simple'] = np.where(va>votes_base, nsa, va/votes_base*nsa)
    df['bayesian'] = nsa*va/(va+votes_prior)+rating_prior*votes_prior/(va+votes_prior)
    exp = log(va.max())
    df['hot'] = np.log(va)/exp*nsa
    weight = 1.959964
    df['wilson']=((nsa + (weight * weight) / (2 * va)) - (weight / (2 * va)) * np.sqrt(4 * va * nsa * (1 - nsa) + (weight * weight))) / (1 + (weight * weight) / va)
    n0 = df['simple'].rank(method='min', ascending=False, pct=True)
    n1 = df['bayesian'].rank(method='min', ascending=False, pct=True)
    n2 = df['hot'].rank(method='min', ascending=False, pct=True)
    n3 = df['wilson'].rank(method='min', ascending=False, pct=True)
    df['n'] = np.where((n0 < ratio) | (n1 < ratio) | (n2 < ratio) | (n3 < ratio), 100-np.floor(n1.values*100), np.nan)
    if sort_type == 'bayesian':
        df.sort_values(by=['n','bayesian'], inplace=True, ascending=(False,False))
    elif sort_type == 'simple':
        df.sort_values(by=['n','simple',votes_col], inplace=True, ascending=(False,False,False))
    ext = save_path.split('.')[-1]
    if ext == 'xlsx':
        df.to_excel(save_path, index=False)
    elif ext == 'csv' or 'txt':
        df.to_csv(save_path, index=False)


def func():
    begin = time.time()
    while True:
        time.sleep(1)
        system('cls')
        print(int(time.time()-begin))


# Thread(target=func, daemon=True).start()
rank('data.csv')