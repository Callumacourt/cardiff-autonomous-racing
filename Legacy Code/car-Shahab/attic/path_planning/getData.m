function res = getData()
    Name = {'Jones';'Brown'};
    Age = [40;49];
    data = table(Name, Age)
    res = jsonencode(data)
end 