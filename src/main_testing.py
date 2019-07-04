import argparse
import logging
import os
from src.state import *
from src.database import *
import csv

"""
A "main" created for testing purposes

"""


def make_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='../join-order-benchmark/queries',
                        help='Define the relative path of the dataset directory')

    return parser.parse_args()


def print_config(args):
    print("Running with the following configuration")
    arg_map = vars(args)
    for key in arg_map:
        print('\t', key, '->', arg_map[key])


def get_times():
    args = make_args_parser()
    db = Database()
    files = os.listdir(args.dataset)
    results = []
    for file_name in files:
        file = open(args.dataset + "/" + file_name, 'r')
        query = file.read()

        planning, execution = db.get_query_time(query)
        cost = db.optimizer_cost(query)
        results.append((file_name, planning, execution, cost))
        print(file_name, "Planning time:", planning, "Execution time:", execution, 'Cost:', cost)

        with open('times.csv', 'w', newline='') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['query', 'planning', 'execution', 'cost'])
            for row in results:
                csv_out.writerow(row)
        # break


def main():
    args = make_args_parser()
    # print_config(args)

    db = Database()
    row = db.get_tables_attributes()

    tables_attributes = {}
    for table, attribute in row:
        if table in tables_attributes:
            tables_attributes[table].append(attribute)
        else:
            tables_attributes[table] = [attribute]

    tables = list(tables_attributes.keys())
    # print(tables)
    attributes = []
    for k in tables_attributes:
        attributes = attributes + [k + "." + v for v in tables_attributes[k]]
    # print(attributes)

    files = os.listdir(args.dataset)
    for file_name in files:
        file = open(args.dataset + "/" + file_name, 'r')

        query = file.read()

        initial_state = StateVector(query, tables, attributes)
        #print(initial_state.join_predicates)
        #print(initial_state.selection_predicates)

        # print(query)
        # print(db.get_query_time(query))
        break
    #get_times()
    db.close()

    # drl_model = Model()
    # drl_model.train(dataset, hyperparameters)
    # drl_model.save()


# def action_space():
#     #jp = self.observation_space[1]
#     #states = self.observation_space[0]
#     jp = [
#         [0, 0, 1, 0],
#         [0, 0, 1, 1],
#         [1, 1, 0, 0],
#         [0, 1, 0, 0],
#     ]
#     states = [
#         [1/2, 0, 1/2, 0],
#         [0, 1, 0, 0],
#         [0, 0, 0, 1],
#         #[0, 0, 0, 1],
#     ]
#     action_space = []
#     for i in range(0, len(states)):
#         for j in range(i + 1, len(states)):
#             for idx1, val1 in enumerate(states[i]):
#                 for idx2, val2 in enumerate(states[j]):
#                     if val1 != 0 and val2 != 0 and jp[idx1][idx2] == 1:
#                         action_space.append((i, j))
#
#     print(action_space)
#     return True


if __name__ == '__main__':
    main()