function [recall, specificity, precision, F1, accuracy, balanced_accuracy] = interpret_conf(conf)

recall = conf(2, 2) / (conf(2, 2) + conf(2, 1));
specificity = conf(1, 1) / (conf(1, 1) + conf(1, 2));
precision = conf(2, 2) / (conf(1, 2) + conf(2, 2));
F1 = 2 * conf(2, 2) / (2 * conf(2, 2) + conf(1, 2) + conf(2, 1));
accuracy = (conf(1, 1) + conf(2, 2)) / sum(conf(:));
balanced_accuracy = (recall + specificity) / 2;

