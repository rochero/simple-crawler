from scipy.stats import beta
from math import sqrt, log

def get_norm(value, max, min):
    return float(value-min)/float(max-min)

def get_min_sample(conInt=0,pop=0,zVal=1.96):
    if conInt == 0:
        return None
    if pop == 0:
        ss = ((zVal *zVal) * 0.25) / ((conInt / 100) *(conInt / 100))
    else:
        ss = ((zVal *zVal) * 0.25) / ((conInt / 100) *(conInt / 100))
        ss=ss/(1+(ss-1)/pop)
    return int(ss+.5)

def score_beta(score_avg, votes, score_max, score_min, rating_prior, votes_prior):
    # https://medium.com/airy-science/search-ranking-with-bayesian-inference-608275e36ee
    success = get_norm(score_avg, score_max, score_min) * votes
    failure = votes - success
    prior_alpha = get_norm(rating_prior, score_max, score_min) * votes_prior
    prior_beta = votes_prior - prior_alpha
    dist_alpha = prior_alpha + success
    dist_beta = prior_beta + failure
    beta_dist = beta(dist_alpha, dist_beta)
    # Get the lower_beta from probability density function where x < lower_beta 
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

def score_imdb(score_avg, votes, score_max, score_min, rating_prior, votes_prior):
    if score_avg == 0 or votes == 0:
        return 0.0
    rating = get_norm(score_avg, score_max, score_min)
    rating_prior = get_norm(rating_prior, score_max, score_min)
    return float((rating*votes))/float((votes+votes_prior))+float((rating_prior*votes_prior))/float((votes+votes_prior))

def score_wilson(score_avg, votes, score_max, score_min, weight=1.959964):
    if score_avg == 0 or votes == 0:
        return 0.0
    rating = get_norm(score_avg, score_max, score_min)
    return ((rating + (weight * weight) / (2 * votes)) - (weight / (2 * votes)) * sqrt(4 * votes * rating * (1 - rating) + (weight * weight))) / (1 + (weight * weight) / votes)

def score_log(score_avg, votes, score_max, score_min, votes_max):
    if score_avg == 0 or votes == 0:
        return 0.0
    rating = get_norm(score_avg, score_max, score_min)
    return rating*log(votes, votes_max)

print(get_min_sample(5,5e4))