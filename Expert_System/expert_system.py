import tkinter as tk
from tkinter import messagebox
import pandas as pd

# Define the necessary functions for probability calculations
def process_element(lst, num_elem, sign):
    element = lst[num_elem]
    if sign == 'positive' and num_elem == 0:
        element = 1 - element if element < lst[1] else element
    elif sign == 'positive' and num_elem == 1:
        element = 1 - element if element < lst[0] else element
    elif sign == 'negative'and num_elem == 0:
        element = 1 - element if element > lst[1] else element
    elif sign == 'negative'and num_elem == 1:
        element = 1 - element if element > lst[0] else element
    return element

def calculate_pmax(pa_Wj, P_Wj_Xp, P_noWj_Xp):
    return (pa_Wj * P_Wj_Xp) / ((pa_Wj * P_Wj_Xp) + ((1 - pa_Wj) * P_noWj_Xp))

def calculate_pmin(pa_Wj, P_Wj_noXp, P_noWj_noXp):
    return (pa_Wj * P_Wj_noXp) / ((pa_Wj * P_Wj_noXp) + ((1 - pa_Wj) * P_noWj_noXp))

def prob_calculation(method, result_dtfr, orig_data, name_string, num_elem, sign):
    result_data = {}
    for column in orig_data.columns:
        processed_values = orig_data[column][1:].apply(method, args=(num_elem, sign))
        product = processed_values.prod()  # Перемножаем все значения
        result_data[column] = [product]

    result_df = pd.concat([result_dtfr, pd.DataFrame(result_data, index=[name_string])], ignore_index=False)
    return result_df

def calaculate_bayes_positive(p_Wj, P_Xi_Wj, P_Xi_noWj):
    return (p_Wj * P_Xi_Wj) / ((p_Wj * P_Xi_Wj) + ((1 - p_Wj) * P_Xi_noWj) + 1e-20)

def calaculate_bayes_negative(p_Wj, P_Xi_Wj, P_Xi_noWj):
    return (p_Wj * (1 - P_Xi_Wj)) / ((p_Wj * (1 - P_Xi_Wj)) + ((1 - p_Wj) * (1 - P_Xi_noWj)) + 1e-20)

class ProbabilityApp:
    def __init__(self, root, console):
        self.root = root
        self.console = console
        self.root.title("Probability Calculation App")
        
        # Initial DataFrame setup (replace with your actual DataFrame)
        self.df = pd.read_excel(open('tab1.xlsx', 'rb'))
        for column in self.df.columns[1:]:
            self.df[column] = self.df[column].apply(eval)
        self.df.set_index('Unnamed: 0', inplace=True)
        self.df.index.name = None
        
        self.df_copy = self.df.copy()
        self.iter_df = self.df.iloc[0:1]
        self.iter_df.rename(index={'pa(Wj)': 'p(Wj)'}, inplace=True)
        self.iter_df = self.calculate_rest_prob(self.iter_df, self.df)
        
        self.question_index = 1
        
        # GUI Elements
        self.question_label = tk.Label(root, text="")
        self.question_label.pack(pady=20)
        
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side=tk.TOP, anchor='n', padx=20, pady=20)

        self.yes_button = tk.Button(self.button_frame, text="Да", command=lambda: self.answer_question("да"), width=15)
        self.yes_button.pack(side=tk.LEFT, padx=8)

        self.no_button = tk.Button(self.button_frame, text="Нет", command=lambda: self.answer_question("нет"), width=15)
        self.no_button.pack(side=tk.RIGHT, padx=8)
        
        self.update_question()
    
    def reset(self):
        self.df_copy = self.df.copy()
        self.iter_df = self.df.iloc[0:1]
        self.iter_df.rename(index={'pa(Wj)': 'p(Wj)'}, inplace=True)
        self.iter_df = self.calculate_rest_prob(self.iter_df, self.df)
        self.question_index = 1
        self.update_question()
    
    def update_question(self):
        if self.df_copy.shape[0] > 1:
            self.question_label.config(text=f"Вы хотите: {self.df_copy.iloc[self.question_index].name}?")
        else:
            self.display_results()
    
    def answer_question(self, answer):
        if answer == "да":
            sign = "positive"
        elif answer == "нет":
            sign = "negative"
        
        row_name = self.df_copy.iloc[self.question_index].name
        self.iter_df = self.calculate_row_to_df(row_name, self.iter_df, self.df_copy, sign)
        self.df_copy = self.df_copy.drop(row_name)
        
        # Check for small p(Wj) values
        for col in self.iter_df.columns:
            p_Wj_value = self.iter_df.at['p(Wj)', col]
            if p_Wj_value <= 0.0001 and self.df_copy.shape[1] > 1:
                self.iter_df.drop(columns=[col], inplace=True)
                self.df_copy.drop(columns=[col], inplace=True)
        
        self.iter_df = self.calculate_rest_prob(self.iter_df, self.df_copy)
        
        # Check p_max
        for col in self.iter_df.columns:
            p_Wj_value = self.iter_df.at['p(Wj)', col]
            p_max = self.iter_df.at['pmax(Wj)', col]
            if p_max < p_Wj_value:
                self.iter_df.drop(columns=[col], inplace=True)
                self.df_copy.drop(columns=[col], inplace=True)
        if self.console:
            print(self.iter_df)
        
        self.update_question()
    
    def display_results(self):
        self.iter_df = self.iter_df.sort_values(by='p(Wj)', axis=1, ascending=False)
        result_text = ""
        flag = False
        
        for col in self.iter_df.columns:
            p_Wj_value = self.iter_df.at['p(Wj)', col]
            if p_Wj_value < 0.0001 and self.df_copy.shape[1] == 1:
                result_text += f'Вам ничего не подошло'
            
            elif p_Wj_value >= 0.9 or self.df_copy.shape[1] == 1:
                result_text += f'Рекомендованное место:\n---------------------------------\n{col}\nС вероятностью: {p_Wj_value * 100:.2f}%\n---------------------------------\n'
                flag = True
                break
            else:
                if not flag:
                    result_text += f'Рекомендованные места:\n--------------------------------\n'
                    for i, col in enumerate(self.iter_df.columns):
                        if i >= 5:
                            break
                        p_Wj_value = self.iter_df.at['p(Wj)', col]
                        result_text += f'{col}\nС вероятностью: {p_Wj_value * 100:.2f}%\n--------------------------------\n'
                    flag = False
                break
        
        messagebox.showinfo("Results", result_text)
        self.reset()
    
    def calculate_rest_prob(self, result_df, orig_df):
        iter_df = prob_calculation(process_element, result_df, orig_df, 'P(Wj/Xп)', 0, 'positive')
        iter_df = prob_calculation(process_element, iter_df, orig_df, 'P(noWj/Xп)', 1, 'negative')
        iter_df = prob_calculation(process_element, iter_df, orig_df, 'P(Wj/noXп)', 0, 'negative')
        iter_df = prob_calculation(process_element, iter_df, orig_df, 'P(noWj/noXп)', 1, 'positive')
        iter_df.loc['pmax(Wj)'] = iter_df.apply(lambda col: calculate_pmax(col['p(Wj)'], col['P(Wj/Xп)'], col['P(noWj/Xп)']), axis=0)
        iter_df.loc['pmin(Wj)'] = iter_df.apply(lambda col: calculate_pmax(col['p(Wj)'], col['P(Wj/noXп)'], col['P(noWj/noXп)']), axis=0)
        return iter_df

    def calculate_row_to_df(self, row_name, iter_df, df_copy, sign):
        results = {}
        for col in df_copy.columns:
            p_Wj_value = iter_df.at['p(Wj)', col]
            vector = df_copy.at[row_name, col]
            P_Xi_Wj = vector[0]
            P_Xi_noWj = vector[1]
            if sign == 'positive':
                results[col] = calaculate_bayes_positive(p_Wj_value, P_Xi_Wj, P_Xi_noWj)
            elif sign == 'negative':
                results[col] = calaculate_bayes_negative(p_Wj_value, P_Xi_Wj, P_Xi_noWj)
        iter_df = pd.DataFrame(results, index=['p(Wj)'])
        return iter_df

# Initialize and run the app
root = tk.Tk()
app = ProbabilityApp(root, console=True)
root.mainloop()