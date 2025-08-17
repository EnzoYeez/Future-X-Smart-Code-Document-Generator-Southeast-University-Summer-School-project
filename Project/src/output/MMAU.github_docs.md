# 项目 MMAU.github API 文档

## evaluation.py

### string_match(answer, prediction, choices)
- 描述：用于比较答案和预测结果的字符串匹配函数
- 参数：
  - answer (str): 答案字符串
  - prediction (str): 预测结果字符串
  - choices (list): 备选选择列表
- 返回值：布尔值，表示预测结果是否与答案匹配
- 使用示例：
```python
answer = "apple"
prediction = "apple"
choices = ["banana", "orange", "apple"]
result = string_match(answer, prediction, choices)
print(result)  # 输出 True
```

### tokenize(text)
- 描述：将文本进行标记化处理的函数
- 参数：
  - text (str): 待处理的文本字符串
- 返回值：标记化后的单词集合
- 使用示例：
```python
text = "This is a sample text."
tokens = tokenize(text)
print(tokens)  # 输出 {'this', 'is', 'a', 'sample', 'text'}
```

### 注意事项
- 在调用 `string_match` 函数时，确保传入正确的参数类型和格式。
- 在调用 `tokenize` 函数时，传入需要处理的文本字符串。