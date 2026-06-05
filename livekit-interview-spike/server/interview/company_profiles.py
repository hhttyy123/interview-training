from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedCompanyProfile:
    id: str
    name: str
    aliases: tuple[str, ...]
    summary: str
    business_lines: tuple[str, ...]
    products_or_services: tuple[str, ...]
    culture_and_values: tuple[str, ...]
    role_relevant_points: tuple[str, ...]
    interview_talking_points: tuple[str, ...]
    source_notes: tuple[str, ...]
    source_urls: tuple[str, ...]


SEED_COMPANY_PROFILES: tuple[SeedCompanyProfile, ...] = (
    SeedCompanyProfile(
        id="bytedance",
        name="字节跳动",
        aliases=("字节", "bytedance", "抖音", "今日头条"),
        summary="字节跳动是一家以内容平台、推荐技术和全球化产品为核心的互联网科技公司，代表产品包括抖音、今日头条、TikTok 等。",
        business_lines=("内容平台", "短视频与直播", "信息分发", "企业协作与效率工具", "AI 与智能推荐"),
        products_or_services=("抖音", "今日头条", "TikTok", "飞书", "剪映", "豆包"),
        culture_and_values=("追求极致", "务实敢为", "开放谦逊", "坦诚清晰"),
        role_relevant_points=(
            "产品和运营岗位需要理解内容生态、推荐分发、用户增长和商业化之间的关系。",
            "技术岗位需要关注大规模系统、数据驱动、算法体验和工程效率。",
            "面试中适合准备平台治理、内容质量、创作者生态、AI 产品化等话题。",
        ),
        interview_talking_points=("内容生态", "推荐算法", "用户增长", "商业化", "AI 产品化", "全球化"),
        source_notes=("内置公司资料库：基于字节跳动官网与公开资料整理，需定期核验。",),
        source_urls=("https://www.bytedance.com/zh/",),
    ),
    SeedCompanyProfile(
        id="tencent",
        name="腾讯",
        aliases=("腾讯", "tencent", "微信", "qq"),
        summary="腾讯是一家互联网科技公司，业务覆盖社交通讯、数字内容、游戏、金融科技、云与产业互联网等方向。",
        business_lines=("社交通讯", "数字内容", "游戏", "金融科技", "云与产业互联网", "可持续社会价值"),
        products_or_services=("微信", "QQ", "腾讯游戏", "腾讯视频", "腾讯云", "企业微信"),
        culture_and_values=("用户为本", "科技向善", "正直", "进取", "协作", "创造"),
        role_relevant_points=(
            "产品岗位需要理解社交关系链、内容生态、平台规则和商业化平衡。",
            "技术岗位需要关注大规模服务、稳定性、云基础设施和安全。",
            "面试中适合准备消费互联网与产业互联网结合、平台生态和用户价值相关话题。",
        ),
        interview_talking_points=("社交平台", "内容生态", "游戏业务", "云与产业互联网", "科技向善"),
        source_notes=("内置公司资料库：基于腾讯官网公司介绍整理，需定期核验。",),
        source_urls=("https://www.tencent.com/zh-cn/company.html",),
    ),
    SeedCompanyProfile(
        id="alibaba",
        name="阿里巴巴",
        aliases=("阿里", "阿里巴巴", "alibaba", "淘宝", "天猫", "阿里云"),
        summary="阿里巴巴集团以电商、云计算、国际化和数字商业基础设施为核心，使命是让商业更容易。",
        business_lines=("中国电商", "国际数字商业", "本地生活", "菜鸟物流", "阿里云", "大文娱"),
        products_or_services=("淘宝", "天猫", "1688", "阿里云", "菜鸟", "钉钉", "高德"),
        culture_and_values=("客户第一", "员工第二", "股东第三", "创新", "团队合作", "拥抱变化"),
        role_relevant_points=(
            "产品和运营岗位需要理解商家、消费者、平台规则和交易效率。",
            "数据和技术岗位需要关注电商链路、云基础设施、推荐搜索和经营分析。",
            "面试中适合准备平台商业、商家服务、AI 与云、供给侧效率等话题。",
        ),
        interview_talking_points=("平台电商", "商家生态", "云计算", "国际化", "本地生活", "AI 基础设施"),
        source_notes=("内置公司资料库：基于阿里巴巴集团官网和业务介绍整理，需定期核验。",),
        source_urls=("https://www.alibabagroup.com/en-US/about-alibaba-businesses",),
    ),
    SeedCompanyProfile(
        id="meituan",
        name="美团",
        aliases=("美团", "meituan", "大众点评", "美团外卖"),
        summary="美团以本地生活服务为核心，围绕餐饮外卖、到店酒旅、即时配送和零售等场景提升生活服务效率。",
        business_lines=("餐饮外卖", "到店酒旅", "即时配送", "本地零售", "生活服务数字化"),
        products_or_services=("美团外卖", "大众点评", "美团买菜", "美团优选", "美团配送"),
        culture_and_values=("以客户为中心", "长期有耐心", "更好生活", "高效协同"),
        role_relevant_points=(
            "产品和运营岗位需要理解供需匹配、履约效率、商家经营和用户体验。",
            "数据岗位需要关注交易漏斗、配送效率、补贴策略和商家增长。",
            "面试中适合准备本地生活、即时配送、商家数字化和履约体验相关话题。",
        ),
        interview_talking_points=("本地生活", "即时配送", "商家生态", "履约效率", "用户体验"),
        source_notes=("内置公司资料库：基于美团官网公司介绍整理，需定期核验。",),
        source_urls=("https://www.meituan.com/en-US/about-us",),
    ),
    SeedCompanyProfile(
        id="jd",
        name="京东",
        aliases=("京东", "jd", "京东物流", "京东科技"),
        summary="京东以供应链为基础，业务覆盖零售、物流、科技和健康等方向，强调商品、仓配和履约能力。",
        business_lines=("零售电商", "供应链物流", "即时零售", "企业服务", "健康服务"),
        products_or_services=("京东商城", "京东物流", "京东健康", "京东科技", "京东工业"),
        culture_and_values=("客户为先", "诚信", "协作", "创新", "拼搏"),
        role_relevant_points=(
            "产品和运营岗位需要理解供应链效率、履约体验、用户信任和商家经营。",
            "技术岗位需要关注库存、仓配、搜索推荐和交易系统稳定性。",
            "面试中适合准备零售供应链、物流履约和服务体验相关话题。",
        ),
        interview_talking_points=("供应链", "零售电商", "物流履约", "用户信任", "即时零售"),
        source_notes=("内置公司资料库：基于公开资料整理，需接入官方来源后复核。",),
        source_urls=("https://www.jd.com/",),
    ),
    SeedCompanyProfile(
        id="xiaohongshu",
        name="小红书",
        aliases=("小红书", "rednote", "xiaohongshu", "xhs"),
        summary="小红书是生活方式社区平台，用户通过图文和视频分享生活经验、消费决策和兴趣内容。",
        business_lines=("生活方式社区", "内容种草", "社区电商", "品牌营销", "创作者生态"),
        products_or_services=("小红书 App", "蒲公英平台", "品牌合作", "社区电商"),
        culture_and_values=("真实分享", "社区信任", "用户价值", "内容生态"),
        role_relevant_points=(
            "产品和运营岗位需要理解社区氛围、内容治理、创作者生态和商业化边界。",
            "数据岗位需要关注内容推荐、搜索转化、社区互动和品牌投放效果。",
            "面试中适合准备社区信任、种草链路、内容质量和创作者激励相关话题。",
        ),
        interview_talking_points=("生活方式社区", "内容种草", "社区治理", "创作者生态", "品牌商业化"),
        source_notes=("内置公司资料库：基于公开资料整理，需接入官方来源后复核。",),
        source_urls=("https://www.xiaohongshu.com/",),
    ),
)


def search_seed_company_profiles(query: str) -> list[SeedCompanyProfile]:
    clean = query.strip().lower()
    if not clean:
        return list(SEED_COMPANY_PROFILES)
    matches: list[SeedCompanyProfile] = []
    for profile in SEED_COMPANY_PROFILES:
        names = (profile.name, *profile.aliases)
        if any(clean in item.lower() or item.lower() in clean for item in names):
            matches.append(profile)
    return matches


def seed_company_profile_by_query(query: str) -> SeedCompanyProfile | None:
    matches = search_seed_company_profiles(query)
    return matches[0] if matches else None
