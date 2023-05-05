# -*- coding: utf-8 -*-
"""final_preproc_spark.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1CQ5seeSap5E5dTbRHiGQPIZ5tu9usfHg
"""

pip install pyspark

from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark import SparkConf
from pyspark.sql.functions import count

#from pyspark.ml.feature import Tokenizer, HashingTF, IDF 
#from pyspark.ml.classification import LogisticRegression
#from pyspark.ml import Pipeline
from pyspark.sql.functions import col

#sc.stop()
conf = SparkConf().setMaster("local[*]").set("spark.executer.memory", "4g")

sc = SparkContext(conf=conf)
spark = SparkSession(sc).builder.getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

"""**Load all datasets**"""

#"review_id","user_id","business_id","stars","date","text","useful","funny","cool"
#1. Clean the dataset
df_review = spark.read.format("csv").option("header", "true").option("multiline","true").load("/content/drive/MyDrive/yelp_review.csv")

df_review.show()

df_user = spark.read.format("csv").option("header", "true").option("multiline","true").load("/content/drive/MyDrive/yelp_user.csv")

df_user.show()

df_business = spark.read.format("csv").option("header", "true").option("multiline","true").load("/content/drive/MyDrive/yelp_business.csv")

df_business.show()

df_business_attr = spark.read.format("csv").option("header", "true").option("multiline","true").load("/content/drive/MyDrive/yelp_business_attributes.csv")

df_business_attr.show()

from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import csv
try:
    with open("/content/drive/MyDrive/yelp_business_hours.csv", "r") as file:
        reader = csv.reader(file)
        header = next(reader) # extract the header row
        data = [row for row in reader]
    df_business_hr = spark.createDataFrame(data, schema=header)
    
    # Do some processing on the dataframe
    #df_filtered = df_business_hr.filter(col("some_column") == "some_value")
    # Do some more processing on the filtered dataframe
except csv.Error as e:
    print("An error occurred while parsing the CSV file: {}".format(e))
    # Handle the error and move on, for example:
    df_business_hr = spark.createDataFrame([], df_business_hr.schema) # create an empty dataframe with the same schema as df_business_hr
except Exception as e:
    print("An error occurred while processing the data: {}".format(e))
    # Handle the error and move on, for example:
    df_business_hr = spark.createDataFrame([], df_business_hr.schema) # create an empty dataframe with the same schema as df_business_hr

df_business_hr.show()

df_checkin = spark.read.format("csv").option("header", "true").option("multiline","true").load("/content/drive/MyDrive/yelp_checkin.csv")

df_checkin.show()

df_tip = spark.read.format("csv").option("header", "true").option("multiline","true").load("/content/drive/MyDrive/yelp_tip.csv")

df_tip.show()

#Let us print schema for all
df_review.printSchema()

df_review = df_review.withColumn("label", df_review["stars"].cast("double"))
df = df_review.select('text', 'label')

df.show(4)

n_rows = df_review.count()
n_cols = len(df_review.columns)
#Print the shape of the DataFrame
print("Shape of the DataFrame: ({}, {})".format(n_rows, n_cols))

df_review.na.drop("all").show(10, False)

df_review = df_review.na.drop(subset=["stars"])

n_rows = df_review.count()
n_cols = len(df_review.columns)
#Print the shape of the DataFrame
print("Shape of the DataFrame: ({}, {})".format(n_rows, n_cols))

from pyspark.sql.functions import regexp_replace

df_review = df_review.withColumn("stars", regexp_replace("stars", "[^0-9.]+", ""))

df_review.show()

df_review_rating = df_review.filter(df_review.label.isin(1.0,5.0))

df_review_rating.show(4)

n_rows = df_review_rating.count()
n_cols = len(df_review_rating.columns)
#Print the shape of the DataFrame
print("Shape of the DataFrame: ({}, {})".format(n_rows, n_cols))

count_1_star = df_review_rating.filter(df_review_rating.label == 1.0).count()
count_5_star = df_review_rating.filter(df_review_rating.label == 5.0).count()

print("Count of 1-star ratings:", count_1_star)
print("Count of 5-star ratings:", count_5_star)

"""**Barplot**"""

import matplotlib.pyplot as plt
#bar plot
labels = ['1-star', '5-star']
counts = [count_1_star, count_5_star]
plt.bar(labels, counts)

#Add some labels and a title
plt.xlabel('Rating')
plt.ylabel('Count')
plt.title('Count of 1-star vs 5-star Ratings')

#Display the plot
plt.show()

df_review = df_review.withColumn('useful', regexp_replace('useful', '[^0-9]', ''))

df_review = df_review.withColumn('cool', regexp_replace('cool', '[^0-9]', ''))
df_review = df_review.withColumn('funny', regexp_replace('funny', '[^0-9]', ''))

# Select the columns and group by them to count the number of rows in each group
grouped = df_review.select('useful', 'funny', 'cool').groupBy('useful', 'funny', 'cool').count().limit(100)

grouped.show()



"""**Removing stopwords ,tokenizing**"""

# Define the remove_punct() function
def remove_punct(text):
    if text is None:
        return ""
    # remove punctuation from text
    return re.sub(r'[^\w\s]','',text)

import re
from pyspark.sql.functions import udf
import random

#Define the remove_punct() function
def remove_punct(text):
    if text is None:
        return None
    else:
        # remove punctuation from text
        return re.sub(r'[^\w\s]','',text)

#Define the convert_rating() function
def convert_rating(rating):
    rating = int(rating)
    if rating >=4: return 1
    else: return 0

#Define the UDFs
remove_punct_udf = udf(remove_punct)
convert_rating_udf = udf(convert_rating)

#Apply the UDFs to the DataFrame
review_df = df_review_rating.select('review_id','user_id','label', remove_punct_udf('text'), convert_rating_udf('stars')) \
                             .withColumnRenamed('<lambda>(text)', 'text') \
                             .withColumnRenamed('<lambda>(stars)', 'label') \
                             .dropna() \
                             .limit(3002194)

#Show the resulting DataFrame
review_df.show()

from pyspark.ml.feature import Tokenizer
from pyspark.ml.feature import StopWordsRemover

#tokenize
tok = Tokenizer(inputCol="remove_punct(text)", outputCol="words")
review_tokenized = tok.transform(review_df)

#remove stop words
stopword_rm = StopWordsRemover(inputCol='words', outputCol='words_nsw')
review_tokenized = stopword_rm.transform(review_tokenized)

review_tokenized.show(5)

def convert_rating(rating):
    try:
        return int(float(rating))
    except ValueError:
        print(f"Invalid value encountered: {rating}")
        return None

from pyspark.sql.functions import udf
from pyspark.sql.types import IntegerType

#Define the UDF
convert_rating_udf = udf(convert_rating, IntegerType())

#Apply the UDF to the 'stars' column
review_tokenized = review_tokenized.withColumn('convert_rating(stars)', convert_rating_udf('convert_rating(stars)'))

def convert_rating(rating):
    return int(float(rating))

"""**SVM**"""

from pyspark.sql.functions import col, regexp_replace
from pyspark.ml.feature import HashingTF, IDF
from pyspark.ml.classification import LinearSVC
from pyspark.ml import Pipeline

#Remove punctuations from the 'text' column and convert the 'stars' column to numeric type
cleaned_df = review_tokenized.select(regexp_replace(col("convert_rating(stars)"), "[^a-zA-Z\\s]", "").alias("text"), 
                       col("convert_rating(stars)").cast("double"))

#Split the data into training and test sets
train_df, test_df = cleaned_df.randomSplit([0.8, 0.2], seed=42)

#Tokenize the words in the 'text' column and remove stop words
tokenizer = Tokenizer(inputCol="text", outputCol="words")
stopword_remover = StopWordsRemover(inputCol=tokenizer.getOutputCol(), outputCol="words_nsw")

#Create a HashingTF object to create feature vectors from tokenized words
hashingTF = HashingTF(inputCol="words_nsw", outputCol="rawFeatures")

#Create an IDF object to calculate the IDF of each term in the document
idf = IDF(inputCol="rawFeatures", outputCol="features")

#Create a Pipeline object that combines the tokenizer, stopword_remover, HashingTF, and IDF stages
pipeline = Pipeline(stages=[tokenizer, stopword_remover, hashingTF, idf])

"""This SVM model code takes time to run"""

#Fit the pipeline on the training data and transform the test data to get tfidf_df
tfidf_df = pipeline.fit(train_df).transform(test_df)

#Train a SVM model using the tfidf_df
svm = LinearSVC(featuresCol="features", labelCol="convert_rating(stars)")
svm_model = svm.fit(tfidf_df)

from pyspark.ml.evaluation import MulticlassClassificationEvaluator

#Make predictions on the test data using the trained SVM model
predictions = svm_model.transform(tfidf_df)

#Evaluate the predictions using MulticlassClassificationEvaluator
evaluator = MulticlassClassificationEvaluator(predictionCol="prediction", labelCol="convert_rating(stars)", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)

#Print the accuracy
print("Accuracy:", accuracy)



"""**N-GRAM**"""

from pyspark.ml.feature import NGram
from pyspark.sql.functions import col

n = 3  #Change n to the desired value of n for n-grams ,here 3 for trigram
ngram = NGram(n=n, inputCol='words', outputCol='ngram')
add_ngram = ngram.transform(review_tokenized.select(col('words'), col('convert_rating(stars)')))
add_ngram.show(5)

"""N gram modelling takes some time to run"""

from pyspark.ml.classification import LinearSVC
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import CountVectorizer, IDF, VectorAssembler, StringIndexer
from pyspark.sql.functions import col

#create CountVectorizer object
cv_ngram = CountVectorizer(inputCol='ngram', outputCol='tf_ngram')
cvModel_ngram = cv_ngram.fit(add_ngram)
cv_df_ngram = cvModel_ngram.transform(add_ngram)

#create IDF model and transform the data
idf_ngram = IDF(inputCol='tf_ngram', outputCol='tfidf_ngram')
tfidfModel_ngram = idf_ngram.fit(cv_df_ngram)
tfidf_df_ngram = tfidfModel_ngram.transform(cv_df_ngram)

#VectorAssembler to combine features
assembler = VectorAssembler(inputCols=['tfidf_ngram'], outputCol='features')

#convert the label column to a numeric type
label_indexer = StringIndexer(inputCol="convert_rating(stars)", outputCol="label")
label_indexer_model = label_indexer.fit(tfidf_df_ngram)
tfidf_df_ngram = label_indexer_model.transform(tfidf_df_ngram)

#transform the data with the assembler
data = assembler.transform(tfidf_df_ngram).select(['features', 'label'])

#split the data into training and test sets
(train_data, test_data) = data.randomSplit([0.7, 0.3], seed=12345)

#fit SVM model of trigrams
svm = LinearSVC(maxIter=50, regParam=0.3, labelCol='label')
svm_model = svm.fit(train_data)

#make predictions on test data
predictions = svm_model.transform(test_data)

#evaluate the model
evaluator = MulticlassClassificationEvaluator(predictionCol="prediction", labelCol="label", metricName="accuracy")
accuracy = evaluator.evaluate(predictions)
print("Accuracy = %g" % accuracy)

"""Post finding accuracy of two models we will find group of words that occur most frequently in Reviews

"""

#split into training & testing set
splits_ngram = tfidf_df_ngram.select(['tfidf_ngram', 'label']).randomSplit([0.8,0.2],seed=100)
train_ngram = splits_ngram[0].cache()
test_ngram = splits_ngram[1].cache()

from pyspark.mllib.classification import SVMWithSGD
#convert to LabeledPoint vectors
train_lb_ngram = train_ngram.rdd.map(lambda row: LabeledPoint(row[1], MLLibVectors.fromML(row[0])))
test_lb_ngram = train_ngram.rdd.map(lambda row: LabeledPoint(row[1], MLLibVectors.fromML(row[0])))

#fit SVM model of trigrams
numIterations = 50
regParam = 0.3
svm = SVMWithSGD.train(train_lb_ngram, numIterations, regParam=regParam)

import pandas as pd
from pyspark.ml.linalg import Vectors

vocabulary_ngram = cvModel_ngram.vocabulary
coefficients_ngram = svm_model.coefficients.toArray()
svm_coeffs_df_ngram = pd.DataFrame({'ngram': vocabulary_ngram, 'weight': coefficients_ngram}) #ngram and weight table

"""**Top Words occuring in 5 Star review**"""

svm_coeffs_df_ngram.sort_values('weight').head(20)

"""***Top Words occuring in 1 Star review ***"""

svm_coeffs_df_ngram.sort_values('weight', ascending=False).head(20)





