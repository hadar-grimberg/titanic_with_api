# -*- coding: utf-8 -*-
"""
Hadar Grimberg
9/27/2021

"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import normaltest
import warnings
warnings.filterwarnings(action="ignore")

# change pandas  display setting: see all columns when printing and only 2 decimal
pd.set_option('display.max_columns', 500)
pd.options.display.float_format = '{:,.2f}'.format


def load_dataset(path,name):
    # load data and make the PassengerId as the index of the DataFrame
    data=pd.read_csv(path, index_col=0)
    # convert the label, sex & embarked to categorical and Pclass to ordered categorical
    if name == "train":
        data.Survived = data.Survived.astype('category')
    data.Sex = data.Sex.astype('category')
    data.Embarked = data.Embarked.astype('category')
    # explore the columns and the head of the data
    print(f"The head 5 rows of {name} data:\n", data.head(5))
    print (data.info())
    print(data.describe().round(decimals=2))
    return data


def sum_missing_values(train,test):
    # Calculate the total missing values and the percentage of each feature for a table
    def calc_missing_table(df,set):
        total = df.isnull().sum()
        perc = (df.isnull().sum()/len(df))
        # perc = (df.isnull().sum()/len(df)*100).map('{:,.2f}%'.format)
        return pd.concat([total, perc], axis=1, keys=[f'{set} Total',f'{set} percent'])
    # build missing data tables for each dataset's features
    train_missing = calc_missing_table(train.loc[:, train.columns != 'Survived'],"Train")
    test_missing = calc_missing_table(test,"Test")
    # Validate that we have no missing labels
    print(f"There are {train.Survived.isnull().sum()} missing labels")
    return pd.concat([train_missing, test_missing], axis=1).sort_values(by=['Train Total'])

def shared_ticket(dataset):
    ticket_g = dataset.groupby('Ticket')
    dataset["shared_ticket"] = 0
    for name, group in ticket_g:
        if (len(ticket_g.get_group(name)) > 1):
            dataset.loc[ticket_g.get_group(name).index.to_list(), "shared_ticket"] = 1
    dataset["shared_ticket"] = dataset["shared_ticket"].astype('category')
    dataset.drop("Ticket", axis=1, inplace=True)
    return dataset


def initial_visualiztion(dataset):
    # Explore the dataset to find patterns for those who survived and those whom didn't
    # how many survived?
    survived = dataset[dataset.Survived==1]
    died = dataset[dataset.Survived==0]
    s_count = len(survived)
    s_died = len(died)
    s_total = len(dataset)
    print(f"{s_count} survived which provide {s_count/s_total:.2f}% of the data\n{s_died} didn't survived which provide {s_died/s_total:.2f}% of the data")

    # Nominal feature examination:
    ## No need to examine name/last name for now, because there are other features that
    # indicate if there was a family member on board. More than half of the values of Cabine are
    # missing thus it won't be examinate. Interesting many passangers had a shared ticket
    print(f"{dataset['Ticket'].nunique()} of {dataset['Ticket'].count()}  ticket numbers are unique")

    # Create new feature that indicates whether the passenger had a shared ticket or no, it will be used for furfur analysis
    dataset = shared_ticket(dataset)

    # Numerical and categorical feature examination:
    numcat_feat = dataset.select_dtypes(exclude=[object]).columns.to_list()
    numcat_feat.remove('Survived')
    visualiztion_dashboard(dataset, numcat_feat, "Survived", survived, died)

    """Conclusions:
    Age: It's seem that young children (ages 0-10) had a better survival rate.
        However, young adults (ages 18 - 30-ish) had a worse survival rate
        Also, there are no obvious outliers that would indicate problematic input data.
    Fare: The survival chances were much lower for the cheaper cabins.    
    Pclass: It seem that the higher the class the passenger beloned to, the chances to survive
            are better. Corresponding to the fare's pattern
    SibSp: Having 1-2 siblings/spouses on board increases better survival odds
    Parch: Having 1-3 parents/children on board increases better survival odds
    Embarked: Intuitively, this is a variable that does not affect the chances of survival.
            Embarking at "C" resulted in a higher survival rate than embarking at "Q" or "S".
    shared_ticket: Having a shared ticket increases better survival odds """

    # Check for normality
    numeric_features = dataset.select_dtypes(include=[np.number]).columns.to_list()
    numeric_features.remove('Survived')
    normal_features = normality_check(dataset[numeric_features])

    # Pearson correlations for normal distributed features
    if normal_features:
        plt.figure(figsize=(14, 12))
        sns.heatmap(dataset[normal_features].corr(), square=True, annot=True,  fmt = ".2f", cmap = "coolwarm", vmin=-1, vmax=1)
        plt.title("Pearson Correlations")
        plt.show()
    # Spearman correlation for other  distributed features
    plt.figure(figsize=(14, 12))
    sns.heatmap(dataset.drop(normal_features, axis=1).corr(method="spearman"), square=True, annot=True,  fmt = ".2f", cmap = "coolwarm", vmin=-1, vmax=1)
    plt.title("Spearman Correlations")
    plt.show()


    """Conclusions:
    Pclass is highly reverse correlated with Fare and reverse moderately correlated with Age 
    (higher class tickets are more expensive, and attributed to higher age).
    SibSp, Parch and Fare are moderately correlated (large families would have high values for both and higher fare).
    Survived is moderately correlates with Fare and with reversed Pcalss (the higher the class and the fare, it is more likely to survive)"""

    return dataset


def visualiztion_dashboard(dataset,features,labels,pos_labels_data, neg_labels_data):
    # Create summary visualiztion dashboard
    # convert the labels to int for visualization
    dataset[labels]=dataset[labels].astype('int')
    sp=331
    plt.figure(figsize=[12, 10])
    # loop over features to create visualization
    for feature in features:
        if dataset[feature].dtype == np.float:
        # float means it is a continuous variable, hence we can check the normality of distribution
            if (dataset[feature].skew()>2) | (dataset[feature].skew()<=-2):
                # this is a very sided skew, the mean is influenced by small
                # portion of extreme values. Hence, Logarithmic transformation is needed
                plt.subplot(sp)
                sns.distplot(np.log10(pos_labels_data[feature].dropna().values + 1), kde=False, color="green", label='Survived')
                sns.distplot(np.log10(neg_labels_data[feature].dropna().values + 1), kde=False, color="red", axlabel=feature, label='Not Survived')
                plt.legend()
            else:
                plt.subplot(sp)
                sns.distplot(pos_labels_data[feature].dropna().values, bins=range(int(dataset[feature].min()), int(dataset[feature].max()), 1), kde=False, color="green", label='Survived')
                sns.distplot(neg_labels_data[feature].dropna().values, bins=range(int(dataset[feature].min()), int(dataset[feature].max()), 1), kde=False, color="red",
                     axlabel=feature, label='Not Survived')
                plt.legend()
        else:
            plt.subplot(sp)
            sns.barplot(x=feature, y=labels, data=dataset)
        sp+=1
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.95, hspace=0.25, wspace=0.35)
    plt.show()


def cross_sex_age(dataset):
    msurv = dataset[(train['Survived'] == 1) & (dataset['Sex'] == "male")]
    fsurv = dataset[(train['Survived'] == 1) & (dataset['Sex'] == "female")]
    mnosurv = dataset[(train['Survived'] == 0) & (dataset['Sex'] == "male")]
    fnosurv = dataset[(train['Survived'] == 0) & (dataset['Sex'] == "female")]

    plt.figure(figsize=[13, 5])
    plt.subplot(121)
    sns.distplot(fsurv['Age'].dropna().values, bins=range(0, 81, 1), kde=False, color="green")
    sns.distplot(fnosurv['Age'].dropna().values, bins=range(0, 81, 1), kde=False, color="red",
                 axlabel='Female Age')
    plt.subplot(122)
    sns.distplot(msurv['Age'].dropna().values, bins=range(0, 81, 1), kde=False, color="green")
    sns.distplot(mnosurv['Age'].dropna().values, bins=range(0, 81, 1), kde=False, color="red",
                 axlabel='Male Age')
    """
    Conclusions:
    For females the probability of survival are better between 18 and 40 years old,
    whereas the probability of survival for men in that age ranfe is lower. The difference
    between women and men in these ages might be a better feature than Sex and Age by themselves.
    Boys have better survival chances than men, whereas girls have similar chances as women have."""

# Check whether each feature is normally distributed
def normality_check(data):
    normal_features=[]
    for col in data.columns:
        s, p = normaltest(data[col][data[col].notnull()])
        if p>=0.05:
            normal_features.append(col)
    return normal_features

def fill_missing_by_mode(train_,test_,features):
    train=train_.copy()
    test=test_.copy()
    # fill missing data by the mode of other passengers with same sex, class and similar age (if age existed)
    for f in features:
        train_null_idx = train[train[f].isnull()].index.to_list()
        test_null_idx = test[test[f].isnull()].index.to_list()
        if train_null_idx:
            train.loc[train_null_idx, f] = train.loc[train_null_idx, :].apply(lambda row:
            (train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass) &
            (row.Age - 10 >= train['Age']) & (train['Age'] <= row.Age + 10)].mode())
            if not pd.isna(row.Age) else train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass)].mode(), axis=1).values
            print(f"{len(train_null_idx)} {f} missing values filled with mode within the train set")
        if test_null_idx:
            test.loc[test_null_idx, f] = test.loc[test_null_idx, :].apply(lambda row:
            (train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass) &
            (row.Age - 10 >= train['Age']) & (train['Age'] <= row.Age + 10)].mode())
            if not pd.isna(row.Age) else train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass)].mode(), axis=1).values
            print(f"{len(test_null_idx)} {f} missing values filled with mode within the test set")
    return train,test

def fill_missing_by_median(train_,test_,features):
    train=train_.copy()
    test=test_.copy()
    # fill missing data by the median of other passengers with same sex, class and similar age (if age existed)
    for f in features:
        train_null_idx = train[train[f].isnull()].index.to_list()
        test_null_idx = test[test[f].isnull()].index.to_list()
        if train_null_idx:
            train.loc[train_null_idx, f] = train.loc[train_null_idx, :].apply(lambda row:
            (train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass) &
            (row.Age - 10 >= train['Age']) & (train['Age'] <= row.Age + 10)].median())
            if not pd.isna(row.Age) else train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass)].median(), axis=1).values
            print(f"{len(train_null_idx)} {f} missing values filled with median within the train set")
        if test_null_idx:
            test.loc[test_null_idx, f] = test.loc[test_null_idx, :].apply(lambda row:
            (train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass) &
            (row.Age - 10 >= train['Age']) & (train['Age'] <= row.Age + 10)].median())
            if not pd.isna(row.Age) else train[f][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass)].median(), axis=1).values
            print(f"{len(test_null_idx)} {f} missing values filled with median within the test set")
    return train,test

def fill_missing_age_by_median(train_,test_):
    train=train_.copy()
    test=test_.copy()
    train["title"] = train['Name'].str.split(", ", expand=True)[1].str.split(".", expand=True)[0]
    test["title"] = test['Name'].str.split(", ", expand=True)[1].str.split(".", expand=True)[0]
    titles = train[["title", "Survived"]].groupby("title").count()[train[["title", "Survived"]].groupby("title").count().sort_values(
        "Survived", ascending=False) > 30].dropna().index.to_list()

    # fill missing data by the median of other passengers with same sex, class and similar title (if title existed)
    train_null_idx = train[train["Age"].isnull()].index.to_list()
    test_null_idx = test[test["Age"].isnull()].index.to_list()
    if train_null_idx:
        train.loc[train_null_idx, "Age"] = train.loc[train_null_idx, :].apply(lambda row:
        (train["Age"][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass) &
        (row.title == train['title'])].median()) if row.title in titles
        else train["Age"][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass)].median(), axis=1).values
        print(f"{len(train_null_idx)} age missing values filled with median within the train set")
    if test_null_idx:
        test.loc[test_null_idx, "Age"] = test.loc[test_null_idx, :].apply(lambda row:
        (train["Age"][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass) &
        (row.title == train['title'])].median()) if row.title in titles
        else train["Age"][(train['Sex'] == row.Sex) & (train['Pclass'] == row.Pclass)].median(), axis=1).values
        print(f"{len(test_null_idx)} age missing values filled with median within the test set")
    train.drop(["Name", "title"], inplace=True, axis=1)
    test.drop(["Name", "title"], inplace=True, axis=1)
    return train,test

# Outlier detection - visualization
def Box_plots(df,col):
    plt.figure(figsize=(10, 4))
    plt.title(f"Box Plot of {col}")
    sns.boxplot(data=df)
    plt.show()

# Outlier detection
def detect_outliers(df):
    """
    Takes a dataframe df of features and returns a list of the indices
    of observations that containing outliers according to the Tukey method.
    """
    outlier_indices = {}
    # iterate over features(columns)
    for col in df.columns:
        # 1st quartile (25%)
        Q1 = np.percentile(df[col].dropna(), 25)
        # 3rd quartile (75%)
        Q3 = np.percentile(df[col].dropna(), 75)
        # Interquartile range (IQR)
        IQR = Q3 - Q1

        # outlier step
        outlier_step = 1.5 * IQR

        # Determine a list of indices of outliers for feature col
        outlier_list_col = df[(df[col] < Q1 - outlier_step) | (df[col] > Q3 + outlier_step)].index.to_list()

        # append the found outlier indices for col to the list of outlier indices
        outlier_indices[col]=outlier_list_col
        if outlier_list_col:
            Box_plots(df[col],col)
    return outlier_indices

# print(train.isnull().sum())
# print(test.info())


if __name__ == '__main__':
    # Load train data and preliminary examination
    train = load_dataset(r"..\data\train.csv","train")
    """from first examination of the train set, one may see that there are many nulls within Age and Cabin.
    The mean age is 28 and 50% of the passengers are between 20 to 38 years old. At least 75% of the passengers
    hadn't parents or children on board and at least 50% of the passengers hadn't siblings/spouse on board.
    The mean fare was 32.2 which is ~6% of the maximum fare, less than 25% paid fare of above the average."""

    # Load test data and preliminary examination
    test = load_dataset(r"..\data\test.csv","test")
    """from first examination of the test set, one may see that there are many nulls within Age and Cabin as seen
     in train set. Mean age is 30.27, a little bit higher than in train set. At least 75% of the passengers
    hadn't parents or children on board and at least 50% of the passengers hadn't siblings/spouse on board, like 
    the train set. The mean fare was 35.63 which is ~7% of the maximum fare, less than 25% paid fare of above the average."""

    # initial exploarion of the labels and features one by one and try to find patterns
    # in order to solve our goal. The folowing function enable to examine and compare
    # distributions of survivors and non-survivors by visualization
    train = initial_visualiztion(train)
    # Add the new shared_ticket feature to the testset as well
    test = shared_ticket(test)

    ## Handling the missing data
    # Accurate assessment of the missing data
    missing_vals = sum_missing_values(train,test)
    """Age feature has about 180 nulls
    and Cabin feature has about 690 nulls, there ar no other nulls in the train set.
    The Name contains titles that indicate a certain age group. It might be use to fill the missing data"""

    # handle with missing categorical data where less than 25% of the values are missing
    cat_few=missing_vals[(((missing_vals['Test percent']<0.25)&(missing_vals['Test percent']>0)) | ((missing_vals['Train percent']<0.25)&(missing_vals['Train percent']>0)))&(train.dtypes=="category")].index.to_list()
    train, test = fill_missing_by_mode(train,test,cat_few)

    # handle with missing numeric data where less than 25% of the values are missing
    numeric_features = [col for col in train.select_dtypes(include=np.number).columns.tolist() if col not in ['Survived', 'Age']]
    num_few = missing_vals.loc[numeric_features,:][(((missing_vals['Test percent'] < 0.25) & (missing_vals['Test percent'] > 0)) | (
                (missing_vals['Train percent'] < 0.25) & (missing_vals['Train percent'] > 0)))].index.to_list()
    train, test = fill_missing_by_median(train, test, num_few)
    # handle age missing data
    train, test = fill_missing_age_by_median(train,test)

    # drop features with 25% or more missing values
    train.drop(missing_vals[missing_vals['Train percent']>=0.25].index.to_list(), axis=1, inplace=True)
    test.drop(missing_vals[missing_vals['Test percent']>=0.25].index.to_list(), axis=1, inplace=True)


    # Join train and test datasets in order to clean both datasets at once and to obtain
    # the same number of features during categorical conversion
    dataset =  pd.concat(objs=[train, test], axis=0).reset_index(drop=True)


    # detect outliers for numerical features

    # Outliers_to_drop = detect_outliers(train[numeric_features])