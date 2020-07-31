import pandas

# # df now has two columns: name and country
# df = pandas.DataFrame({
#         'name': ['josef','michael','john','bawool','klaus'],
#         'country': ['russia', 'germany', 'australia','korea','germany']
#     })

# # use pandas.concat to join the new columns with your original dataframe
# df = pandas.concat([df,pandas.get_dummies(df['country'], prefix='country')],axis=1)

# # now drop the original 'country' column (you don't need it anymore)
# df.drop(['country'],axis=1, inplace=True)

# print(df)

df = pandas.read_csv('./data/features_and_scores.csv')

def calculate_good_bad(score):
    if score > 3:
        return 'Bad'
    else:
        return 'Good'

df['GoodBad'] = df.Score.apply(calculate_good_bad)

print(df)