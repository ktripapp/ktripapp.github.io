---
layout: default
title: Home
---

<h1>{{ site.title }}</h1>
<p>{{ site.description }}</p>

<ul>
{% raw %}{% for post in site.posts %}{% endraw %}
  <li><a href="{{ post.url }}">{{ post.title }}</a> — {{ post.date | date: "%Y-%m-%d" }}</li>
{% raw %}{% endfor %}{% endraw %}
</ul>
