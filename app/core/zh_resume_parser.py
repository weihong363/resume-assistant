import spacy
import jionlp as jio
from flashtext import KeywordProcessor
import re
from datetime import datetime

# 加载 spaCy 中文模型
try:
    # 使用 transformer 模型提高准确性
    nlp = spacy.load('zh_core_web_trf')
except OSError:
    nlp = spacy.load('zh_core_web_sm')
class ChineseResumeParser:
    def __init__(self):
        # 初始化技能关键词处理器 (比正则快100倍)
        self.skill_processor = KeywordProcessor(case_sensitive=False)
        self._init_skill_keywords()
        
        # 初始化公司后缀关键词
        self.company_suffixes = KeywordProcessor()
        self.company_suffixes.add_keywords_from_list(['有限公司', '科技公司', '集团', '股份公司', '研究所'])
        
        # 教育机构关键词
        self.edu_keywords = KeywordProcessor()
        self.edu_keywords.add_keywords_from_list(['大学', '学院', '学校'])
        
        # 预编译正则
        self.date_pattern = re.compile(r'(\d{4}年\d{1,2}月|\d{4}\.\d{1,2}|\d{4}-\d{2})')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b1[3-9]\d{9}\b')
        
        # 中文停用词增强
        self.stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就']) | set(spacy.lang.zh.STOP_WORDS)
    
    def _init_skill_keywords(self):
        """加载IT行业技能关键词"""
        skills = [
            # 编程语言
            'Python', 'Java', 'JavaScript', 'C++', 'Go', 'TypeScript', 'SQL',
            # 前端框架
            'React', 'Vue', 'Angular', 'jQuery', 'Bootstrap',
            # 后端框架
            'Django', 'Flask', 'Spring', 'Node.js', 'Express', 'FastAPI',
            # 数据库
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle', 'SQLite',
            # 云服务
            'AWS', '阿里云', '腾讯云', 'Docker', 'Kubernetes', 'Azure',
            # 数据科学
            'Pandas', 'NumPy', 'Scikit-learn', 'TensorFlow', 'PyTorch', '数据分析',
            # 开发工具
            'Git', 'Jenkins', 'Linux', 'Shell', 'RESTful API', '微服务'
        ]
        self.skill_processor.add_keywords_from_list(skills)
        
        # 添加同义词映射
        self.skill_processor.add_keyword('JS', 'JavaScript')
        self.skill_processor.add_keyword('NLP', '自然语言处理')
        self.skill_processor.add_keyword('CV', '计算机视觉')
    
    def parse(self, resume_text):
        """解析简历文本"""
        # 基础文本清理
        clean_text = self._clean_text(resume_text)
        doc = nlp(clean_text)
        
        # 提取各个部分
        result = {
            "name": self._extract_name(doc),
            "contact": self._extract_contact(clean_text),
            "skills": self._extract_skills(clean_text),
            "education": self._extract_education(doc),
            "experience": self._extract_experience(doc),
            "projects": self._extract_projects(doc)
        }
        
        return result
    
    def _clean_text(self, text):
        """清理简历文本"""
        # 移除特殊字符但保留中文标点
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。；：？！、（）《》【】]', '', text)
        # 合并连续空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_name(self, doc):
        """提取中文姓名 (使用JioNLP的增强功能)"""
        # 方法1：使用JioNLP的姓名提取
        name_info = jio.extract_chinese(doc.text)[0]
        if name_info and 'name' in name_info:
            return name_info['name']
        
        # 方法2：规则匹配
        for ent in doc.ents:
            if ent.label_ == "PERSON" and 2 <= len(ent.text) <= 4:
                return ent.text
        
        # 方法3：查找"姓名"标签
        for token in doc:
            if token.text in ['姓名', '名字'] and token.i+1 < len(doc):
                return doc[token.i+1].text
                
        return "未识别"
    
    def _extract_contact(self, text):
        """提取联系方式"""
        emails = set(self.email_pattern.findall(text))
        phones = set(self.phone_pattern.findall(text))
        
        # 提取微信 (中文简历常见)
        wechat_matches = re.findall(r'微信[:：]?\s*([a-zA-Z0-9_-]{6,20})', text)
        wechats = set(wechat_matches)
        
        return {
            "emails": list(emails),
            "phones": list(phones),
            "wechat": list(wechats)[0] if wechats else ""
        }
    
    def _extract_skills(self, text):
        """提取技能 (使用FlashText快速匹配)"""
        found_skills = self.skill_processor.extract_keywords(text)
        
        # 去重并过滤停用词
        skills = set()
        for skill in found_skills:
            # 标准化技能名称 (使用同义词映射)
            normalized = self.skill_processor.get_keyword(skill)
            if normalized not in self.stopwords and len(normalized) >= 2:
                skills.add(normalized)
        
        return list(skills)
    
    def _extract_education(self, doc):
        """提取教育经历"""
        edu_sections = []
        current_edu = {}
        
        # 使用JioNLP解析时间
        time_infos = jio.parse_time([sent.text for sent in doc.sents], time_base=datetime.now().year)
        
        for sent in doc.sents:
            text = sent.text
            
            # 检测教育机构
            if self.edu_keywords.extract_keywords(text):
                if current_edu:
                    edu_sections.append(current_edu)
                    current_edu = {}
                
                # 提取学校名称 (取包含教育关键词的最长名词短语)
                for np in sent.noun_chunks:
                    if any(kw in np.text for kw in ['大学', '学院']):
                        current_edu['institution'] = np.text
                        break
            
            # 检测时间范围
            if 'date_range' not in current_edu:
                for time_info in time_infos:
                    if time_info['text'] in text and 'time' in time_info:
                        current_edu['date_range'] = time_info['time']
                        break
            
            # 检测学位/专业
            if 'degree' not in current_edu:
                degree_keywords = ['学士', '硕士', '博士', '本科', '研究生', 'MBA', '博士']
                for token in sent:
                    if token.text in degree_keywords:
                        current_edu['degree'] = token.text
                        # 尝试提取专业
                        for child in token.children:
                            if child.dep_ == 'nmod' and child.pos_ == 'NOUN':
                                current_edu['major'] = child.text
        
        if current_edu:
            edu_sections.append(current_edu)
        
        return edu_sections
    
    def _extract_experience(self, doc):
        """提取工作经历"""
        experiences = []
        current_exp = {}
        in_experience_section = False
        
        for i, sent in enumerate(doc.sents):
            text = sent.text
            
            # 检测工作经历部分开始
            if "工作经历" in text or "工作经验" in text:
                in_experience_section = True
                continue
                
            if not in_experience_section:
                continue
                
            # 检测公司名称 (使用公司后缀关键词)
            if not current_exp or 'company' not in current_exp:
                company_matches = self.company_suffixes.extract_keywords(text)
                if company_matches:
                    # 提取包含公司后缀的名词短语
                    for np in sent.noun_chunks:
                        if any(suffix in np.text for suffix in company_matches):
                            current_exp['company'] = np.text
                            break
            
            # 检测时间范围
            if 'date_range' not in current_exp:
                matches = self.date_pattern.findall(text)
                if matches:
                    current_exp['date_range'] = matches[0]
            
            # 检测职位
            if 'position' not in current_exp:
                position_keywords = ['工程师', '开发', '架构师', '经理', '总监', '分析师']
                for token in sent:
                    if token.text in position_keywords:
                        # 提取职位名词短语
                        current_exp['position'] = token.head.text
                        break
            
            # 段落结束或新公司出现时保存当前经历
            if len(text.strip()) < 10 or (i < len(list(doc.sents))-1 and self.company_suffixes.extract_keywords(list(doc.sents)[i+1].text)):
                if current_exp:
                    experiences.append(current_exp)
                    current_exp = {}
        
        return experiences
    
    def _extract_projects(self, doc):
        """提取项目经历"""
        projects = []
        current_proj = {}
        in_project_section = False
        
        for sent in doc.sents:
            text = sent.text
            
            # 检测项目部分开始
            if "项目经历" in text or "项目经验" in text:
                in_project_section = True
                continue
                
            if not in_project_section:
                continue
                
            # 检测项目标题 (通常包含冒号或项目编号)
            if not current_proj or 'title' not in current_proj:
                if re.search(r'项目[名称]?[:：]', text) or re.search(r'^[0-9]+\.', text):
                    title = re.sub(r'项目[名称]?[:：]\s*', '', text).strip()
                    title = re.sub(r'^[0-9]+\.\s*', '', title)
                    current_proj['title'] = title
                    continue
            
            # 检测技术关键词
            if 'technologies' not in current_proj:
                techs = self.skill_processor.extract_keywords(text)
                if techs:
                    current_proj['technologies'] = list(set(techs))
            
            # 项目描述累积
            if 'description' not in current_proj:
                current_proj['description'] = text
            else:
                current_proj['description'] += " " + text
                
            # 简单分段逻辑
            if len(text) < 50 or sent.text.endswith('。'):
                if current_proj and 'title' in current_proj:
                    projects.append(current_proj)
                    current_proj = {}
        
        return projects