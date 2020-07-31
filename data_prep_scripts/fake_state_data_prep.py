import random
import pandas

states = []

with open('./data/states.csv') as file:
    for line in file:
        states.append(line[:2])

# print(states)

# for i in range(100):
#     print(random.choice(states))

faers_filename = './data/faers_261.csv'

df = pandas.read_csv(faers_filename, index_col = 0)

df['Fake State'] = df.apply(lambda row: random.choice(states), axis = 1)

df.to_csv('./data/faers_261_with_fake_states.csv')