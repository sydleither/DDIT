# A data-driven information theory framework.
# Allows the computation and composition of shannon entropy and mutual information.
# Data is stored and manipulated as columns/rows of variable states; entropy is calculated from collapsing these tables
# Alternate probability estimators are supported
# 
# Vincent Ragusa 2019
# 


#TODO replace all accesses of self.columns with the new get/set functions. Then add a flag to have each entry in the dict a file instead to conserve RAM


from numpy import log2, isclose, array, memmap
from copy import deepcopy	
import datetime

class DDIT:

    def __init__(self, probability_estimator="maximum_likelihood", verbose=False):
        self.raw_data = None
        self.labels = None
        self.__columns = {}
        self.entropies = {}
        self.column_keys = set()
        self.max_states = {}
        self.probability_estimator = probability_estimator
        # "james-stein"
        self.verbose = verbose


    def __get_column(self, key):
        return self.__columns[key]

    # def __set_column(self, key, value):
    #     self.__columns[key] = value

    def __set_column_list(self, key, value_list):
        self.__columns[key] = value_list
        self.column_keys.add(key)

    def __remove_column(self,key):
        if self.verbose: print("{} Deleting {} from memory ...".format(str(datetime.datetime.now()),key))
        del self.__columns[key]
        self.column_keys.remove(key)

    def __columns_contains(self, key):
        return key in self.column_keys

    def __columns_empty(self):
        return False if self.column_keys else True


    def load_csv(self, file_path, header=False, auto_regester=False, auto_maximum_states=False):
        if self.verbose: print("{} Loading data from {} ...".format(str(datetime.datetime.now()),file_path))
        with open(file_path, 'r') as csv_file:
            self.raw_data = []
            if header:
                self.labels = csv_file.readline().strip().split(',')
                for line in csv_file:
                    self.raw_data.append(line.strip().split(','))
                if auto_regester:
                    for col, label in enumerate(self.labels):
                        self.register_column(label,col)
                        if auto_maximum_states:
                            self.auto_possible_values(label)
            else:
                for line in csv_file:
                    self.raw_data.append(line.strip().split(','))
                if auto_regester:
                    print("WARNING you must manually regester columns if no header is provided. Skipping auto-regester...")
            if auto_maximum_states and not auto_regester:
                print("WARNING you must automatically regester columns to automatically calculate maximum states. Skipping auto-maximum-states...")


    def register_column(self, key, col, max_states=None):
        if self.verbose: print("{} Registering {} as {} ...".format(str(datetime.datetime.now()), col,key))
        if max_states is not None:
            self.max_states[key] = max_states
        
        if self.__columns_contains(key):
            print("WARNING: column \"{}\" has already been regestered. Overwriting...".format(key))

        new_column = [row[col] for row in self.raw_data]
        self.__set_column_list(key,new_column)


    def register_column_list(self, key, col, max_states=None):

        if max_states is not None:
            self.max_states[key] = max_states
        
        if self.__columns_contains(key):
            print("WARNING: column \"{}\" has already been regestered. Overwriting...".format(key))

        self.__set_column_list(key,col)

    
    def print_columns(self):
        if self.__columns_empty():
            print("No regestered columns to print.")
        else:
            for key in self.column_keys:
                if key in self.max_states:
                    print(key, self.__get_column(key), self.max_states[key])
                else:
                    print(key, self.__get_column(key))
        print()

    
    def AND(self, col1, col2):
        if self.verbose: print("{} Creating joint distribution: {}&{} ...".format(str(datetime.datetime.now()), col1,col2))
        if not self.__columns_contains(col1):
            print("ERROR column \"{}\" is not regestered!".format(col1))
            return
        if not self.__columns_contains(col2):
            print("ERROR column \"{}\" is not regestered!".format(col2))
            return
        key = col1 + "&" + col2
        new_col = [pair for pair in zip(self.__get_column(col1),self.__get_column(col2))]
        if col1 in self.max_states and col2 in self.max_states:
            self.register_column_list(key,new_col, max_states=self.max_states[col1]*self.max_states[col2])
        else:
            self.register_column_list(key,new_col)


    def __james_stein_lambda(self, n, e_counts, p):
        states_recorded = len(e_counts)
        top = 1-sum([(e_counts[event]/n)**2 for event in e_counts])
        bot = (n -1)*(sum([((1/p)-e_counts[event]/n)**2 for event in e_counts]) + (p-states_recorded)*((1/p)**2))
        if bot == 0.0: #prevents divide by 0. assumes x/0 = inf
            return 1.0 # or return 0.0. In either case p_shrink converges to p_ML
        lambda_star = top/bot
        if lambda_star > 1.0: #critical operation! found in appendex A
            lambda_star = 1.0
        return lambda_star


    def H(self, col):
        if not self.__columns_contains(col):
            print("ERROR column \"{}\" is not regestered!".format(col))
            return
        events_data = self.__get_column(col)
        events_recorded = len(events_data)
        event_counts = {}
        for event in events_data:
            if event not in event_counts:
                event_counts[event] = 1
            else:
                event_counts[event] += 1
        h = 0
        for event in event_counts:
            if self.probability_estimator=="maximum_likelihood":
                p = event_counts[event]/ events_recorded
            elif self.probability_estimator=="james-stein":
                if col not in self.max_states:
                    print("ERROR cannot use james-stein probability estimator because \"{}\" does not define maximum states".format(col))
                    return
                lambda_star = self.__james_stein_lambda(events_recorded,event_counts,self.max_states[col])
                t = 1 / self.max_states[col]
                p_ml = event_counts[event]/ events_recorded
                p = lambda_star*t + (1-lambda_star)*p_ml
            else:
                print("ERROR unknown probability estimator \"{}\"".format(self.probability_estimator))
                return
            h -= p * log2(p)

        # if isclose([h],[0]):
        #     return 0
        # else:
        return h


    def I(self, col1, col2):
        and_key = col1 + "&" + col2
        if not self.__columns_contains(and_key):
            if self.verbose: print("{} Regestering column \"{}\"...".format(str(datetime.datetime.now()), and_key))
            self.AND(col1,col2)
        i = self.H(col1) + self.H(col2) - self.H(and_key)
        # if isclose([i],[0]):
        #     return 0
        # else:
        return i

    def auto_possible_values(self, key):
        if self.verbose: print("{} Calculating max states for {}...".format(str(datetime.datetime.now()), key))
        try:
            top = max([float(i) for i in self.__get_column(key)])
            bot = min([float(i) for i in self.__get_column(key)])
            
            sorted_data = sorted(self.__get_column(key))
            list_x = [abs(float(sorted_data[i + 1]) - float(sorted_data[i])) for i in range(len(sorted_data)-1)]
            dif = min(filter(lambda x: x != 0.0, list_x))
            
            if key in self.max_states:
                print("WARNING: column \"{}\" has already specified a maximum number of states. Overwriting...".format(key))
            self.max_states[key] = (top-bot+1)/dif
            if self.verbose: print("{} Max states of {} has been set to {}...".format(str(datetime.datetime.now()), key,self.max_states[key]))
        except:
            print("ERROR: column \"{}\" was not able to be processed by auto_possible_values! Check for non-numeric data.".format(key))


    def __venn_gen_power_set(self, variables, current=[]):
        if variables:
            return self.__venn_gen_power_set(variables[1:],current=current) + self.__venn_gen_power_set(variables[1:], current=current + [variables[0]])
        return [current]

    def __venn_make_formula(self, subset, column_keys):
        if subset:
            subset.sort()
            remainder = sorted(list(set(column_keys) - set(subset)))

            S=""
            S = ":".join(subset)
            if remainder: S += "|"
            # S += "|"
            S += "&".join(remainder)
            return S
        return ""

    def recursively_solve_formula(self, formula, save_memory=False):
        if "|" in formula:
            # formula is a conditional
            halves = formula.split("|")
            if ":" in halves[0]:
                #formula is a conditional with shared entropy on the lhs
                shareds = halves[0].split(":")
                left_formula = ":".join(shareds[1:]) + "|" + halves[1]
                # right_formula = ":".join(shareds[1:]) + "|" + halves[1] + "&" + shareds[0]
                right_formula = ":".join(shareds[1:]) + "|" + "&".join(sorted(halves[1].split("&") + [shareds[0]]))
            else:
                #formula is a conditional of only joints
                # left_formula = halves[0] + "&" + halves[1]
                left_formula = "&".join(sorted(halves[1].split("&") + halves[0].split("&")))
                right_formula = halves[1]

            if left_formula not in self.entropies:
                self.recursively_solve_formula(left_formula, save_memory=save_memory)
            if right_formula not in self.entropies:
                self.recursively_solve_formula(right_formula, save_memory=save_memory)
            
            self.entropies[formula] =  self.entropies[left_formula] - self.entropies[right_formula]
        elif ":" in formula:
            #formula is shared only; treat as special case of above case
            shareds = formula.split(":")
            left_formula = ":".join(shareds[1:])
            right_formula = ":".join(shareds[1:]) + "|" + shareds[0]

            if left_formula not in self.entropies:
                self.recursively_solve_formula(left_formula, save_memory=save_memory)
            if right_formula not in self.entropies:
                self.recursively_solve_formula(right_formula, save_memory=save_memory)
            
            self.entropies[formula] =  self.entropies[left_formula] - self.entropies[right_formula]

        else:
            # formula is only a joint; calculate from data
            # self.__debug_new_count += 1
            variables = formula.split("&")
            if len(variables) == 1:
                self.entropies[formula] = self.H(formula)
            else:
                intermediate = list(zip(self.__get_column(variables[0]), self.__get_column(variables[1])))
                # intermediate_max_states = self.max_states[variables[0]] * self.max_states[variables[1]]
                for var in variables[2:]:
                    intermediate = list(zip(intermediate, self.__get_column(var)))
                    # intermediate_max_states *= self.max_states[var]
                self.register_column_list(formula, intermediate) #,max_states=intermediate_max_states
                self.entropies[formula] = self.H(formula)
                if save_memory:
                    self.__remove_column(formula)
        


    def solve_venn_diagram(self, column_keys=None, save_memory=False):
        if column_keys is None:
            column_keys = list(self.column_keys)
        if self.verbose: print("{} Generating power set of {}...".format(str(datetime.datetime.now()), column_keys))
        power_set = self.__venn_gen_power_set(column_keys)
        if self.verbose: print("{} Generating venn diagram...".format(str(datetime.datetime.now())))
        else: print("Generating venn diagram...")
        for i, subset in enumerate(power_set):
            if i > 0:
                formula = self.__venn_make_formula(subset, column_keys)
                # if self.verbose: print("{}".format(str(datetime.datetime.now())))
                self.recursively_solve_formula(formula,save_memory=save_memory)
                if self.verbose: print("{} {} {} {}".format(str(datetime.datetime.now()),i, formula, self.entropies[formula]))
                else: print("{} {} {}".format(i, formula, self.entropies[formula]))
                # print(i, formula, self.entropies[formula])
                # print("unique formulas calculated: ", self.__debug_new_count)


if __name__ == "__main__":

    # create an instance of the class
    ddit = DDIT(verbose=True)
    
    # auto register columns based on CSV headers 
    ddit.load_csv("xor_data.csv", header=True, auto_regester=True)

    # calculate an arbetrary entropy given in standard form
    ddit.recursively_solve_formula("X:Y|Z")

    # the result is automatically stored in DDIT.entropies
    print("The entropy of X:Y|Z is ", ddit.entropies["X:Y|Z"])

    # get the venn diagram of the system
    ddit.solve_venn_diagram(column_keys=["X","Y","Z"])