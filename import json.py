import json
import re

def parse_full_etymon_data(input_text):
    # 初始化總表
    etymon_db = []
    
    # 分割大類 (例如：「五感與行為」類)
    categories = re.split(r'「(.+?)」類', input_text)
    
    # 因為 split 會把匹配項也留下來，索引 1, 3, 5 是類別名，2, 4, 6 是內容
    for i in range(1, len(categories), 2):
        category_name = categories[i]
        category_content = categories[i+1]
        
        current_category = {
            "category": category_name,
            "root_groups": []
        }
        
        # 尋找詞根區塊 (例如：-dict- (說)：)
        root_blocks = re.split(r'\n(?=-)', category_content)
        
        for block in root_blocks:
            # 匹配詞根名與含義
            root_head = re.search(r'-([\w/ \-]+)-\s*[\(（](.+?)[\)）]', block)
            if root_head:
                root_info = {
                    "roots": root_head.group(1).split('/'),
                    "meaning": root_head.group(2),
                    "vocabulary": []
                }
                
                # 匹配單字、括號內的公式、與解釋
                # 格式：Word (Logic = Translation)
                word_matches = re.findall(r'(\w+[\-\w]*)\s*[\(（](.+?)\s*=\s*(.+?)[\)）]', block)
                for word, logic, trans in word_matches:
                    root_info["vocabulary"].append({
                        "word": word,
                        "breakdown": logic.strip(),
                        "definition": trans.strip()
                    })
                
                if root_info["vocabulary"]:
                    current_category["root_groups"].append(root_info)
        
        etymon_db.append(current_category)
        
    return etymon_db

# 放入你整段「詞根種類」的文字
raw_data = """詞根種類
	「五感與行為」類
		「說」「話「言論」
			-dict- (說)：
				Contradict (Contra 相反 + dict 說 = 矛盾/反駁)
				Predict (Pre 預先 + dict 說 = 預測/預言)
				Verdict (Ver 真實 + dict 說 = 判決/定論)
				Dictator (Dict 說 + ator 人 = 獨裁者/發號施令者)
				Indict (In 進入 + dict 說 = 起訴/控告)
			-log- / -loqu- (說話/言語)：
				Dialogue (Dia 穿過/兩者之間 + log 說 = 對話)
				Apology (Apo 遠離/辯解 + log 說 = 道歉/辯白)
				Eloquent (E 出來 + loqu 說 = 雄辯的/口才流利的)
				Loquacious (Loqu 說 + acious 多...的 = 滔滔不絕的/多話的)
				Monologue (Mono 單一 + log 說 = 獨白)
			-claim- / -clam- (大喊/宣稱)：
				Exclaim (Ex 出去 + claim 喊 = 驚叫/呼喊)
				Proclaim (Pro 向前 + claim 喊 = 宣布/公告)
				Reclaim (Re 回來 + claim 喊 = 拿回/開墾)
			-voc- / -vok- (聲音/召喚)：
				Advocate (Ad 往 + voc 說/聲 = 擁護/提倡)
				Provoke (Pro 向前 + vok 呼喚 = 激怒/挑釁)
				Equivocal (Equi 平等 + voc 聲 = 模稜兩可的/雙關的)
		「看」與「觀察」
			-scop-：觀察/鏡 (Watch/View)。
				Tele-scope (Tele 遠 + scope 觀察 = 望遠鏡)
			-vis- / -vid-：見 (See)。
				In-vis-ible (In 不 + vis 見 = 看不見的)
				Evident (E 出來 + vid 看 = 顯而易見的)
			-spect- / -spic-：看 (Look)。
				Prospect (Pro 前 + spect 看 = 前景)
				Conspicuous (Con 加強 + spic 看 = 顯眼的，大家都在看)
		「聽」與「聲」
			-aud- / -audit- (聽)：
				Audition (Aud 聽 + ition 名詞尾 = 試鏡/聽力)
				Inaudible (In 不 + aud 聽 = 聽不見的)
				Auditorium (Audit 聽 + orium 場所 = 禮堂/聽眾席)
				Auditory (Audit 聽 + ory 形容詞尾 = 聽覺的)
				Audience (Audi 聽 + ence 名詞尾 = 觀眾/聽眾)
			-phon- ：(聲音)
				Symphony (Sym 共同 + phon 聲音 = 交響樂/和聲)
				Cacophony (Caco 惡劣 + phon 聲音 = 雜音/刺耳的聲音)
				Microphone (Micro 微小 + phon 聲音 = 麥克風/擴音器)
				Phonetic (Phon 聲音 + etic 形容詞尾 = 語音的/發音的)
				Homophone (Homo 相同 + phon 聲音 = 同音字)
			-son- (聲音)：
				Resonate (Re 再/加強 + son 聲音 + ate = 共鳴/迴響)
				Sonic (Son 聲音 + ic 形容詞尾 = 音速的/聲音的)
				Unison (Uni 一 + son 聲音 = 一致/齊唱)
				Consonant (Con 共同 + son 聲音 + ant = 子音/和諧的)
		「觸」與「感」
			-tact- / -tang- (接觸)
				Contact (Con 共同 + tact 觸)：接觸、聯繫。
				Tangible (Tang 觸 + ible 可...的)：有形的、可觸知的。
				Intact (In 不 + tact 觸)：原封不動的、未受損傷的（沒被碰過的）。
			-sens- / -sent- (感覺/情感)：
				Sentiment (Sent 感覺 + iment 名詞尾)：感情、情緒。
				Sensory (Sens 感覺 + ory 形容詞尾)：感官的、知覺的。
				Consent (Con 共同 + sent 感覺)：同意（兩個人感覺一致）。
		「嗅」與「味」
			-odor- (氣味)：
				Odorless (Odor 氣味 + less 無)：無味的。
				Deodorant (De 除去 + odor 氣味 + ant 物質)：體香劑、除臭劑。
			-sap- / -sip- (味道/品味/智慧)：
				Insipid (In 不 + sip 味)：枯燥乏味的、淡而無味的。
				Sapient (Sap 味/智慧 + ient)：睿智的（古人認為有品味的人即是有智慧的人）。
		「寫」與「畫」
			-graph- / -gram- (畫/寫/圖表)：
				Autograph (Auto 自己 + graph 寫)：親筆簽名。
				Telegram (Tele 遠 + gram 寫)：電報。
			-scrib- / -scrip- (書寫)：
				Prescribe (Pre 預先 + scribe 寫)：處方、規定（醫生先寫下的指示）。
				Describe (De 下 + scribe 寫)：描寫。
	「移動與空間」類 
		-port- (拿/運/港口)：
			Import (Im 往內 + port 運 = 進口)
			Export (Ex 往外 + port 運 = 出口)
			Portable (Port 拿 + able 可...的 = 手提式的/輕便的)
			Transport (Trans 跨越 + port 運 = 運輸/運送)
			Portfolio (Port 拿 + folio 紙張 = 檔案夾/作品集/投資組合)
			Support (Sup 在下面 + port 撐 = 支持/支撐)
		-tract- (拉/抽)：
			Attract (At 靠近 + tract 拉 = 吸引)
			Extract (Ex 往外 + tract 拉 = 抽出/提煉/萃取)
			Distract (Dis 分散 + tract 拉 = 使分心)
			Contract (Con 共同 + tract 拉 = 契約/收縮 —— 雙方拉到一起簽約)
			Abstract (Ab 離開 + tract 拉 = 抽象的/摘要 —— 從具體中拉出重點)
			Retract (Re 往回 + tract 拉 = 縮回/撤回言論)
		-ced- / -ceed- / -cess- (走/前進)：
			Excess (Ex 超出 + cess 走 = 過度/過剩)
			Precede (Pre 預先 + cede 走 = 在...之前發生)
			Proceed (Pro 向前 + ceed 走 = 繼續進行)
			Recession (Re 往回 + cess 走 = 經濟衰退/後退)
			Concede (Con 全部 + cede 走 = 讓步/承認輸了 —— 全退一步)
			Access (Ac 往 + cess 走 = 管道/進入的權利)
	「心理與生命」類
		-viv- / -vit- (活/生命)：
			Vivid (Viv 活 + id 形容詞尾 = 活生生的/鮮艷的)
			Sur-vive (Sur 超過 + vive 活 = 倖存/活下來)
			Vitality (Vit 生命 + ality 名詞尾 = 活力/生命力)
		-path- (感受/病理)：
			Antipathy (Anti 反 + pathy 感受 = 反感)
			Empathy (Em 進入 + pathy 感受 = 同理心)
			Sympathy (Sym 共同 + pathy 感受 = 同情心)
	「動作與修飾」類
		-fac- / -fec- / -fic- (做/製作)：
			Factory (Fac 做 + tory 場所 = 工廠)
			Efficient (Ex 出來 + fic 做 = 效率高的 —— 能做出成果的)
			Deficit (De 不足 + fic 做 = 赤字/不足額)
			Magnificent (Magni 大 + fic 做 = 宏偉的/極好的)
		-cap- / -cept- / -ceive- (拿/取/收)：
			Capture (Capt 拿 + ure 名詞尾 = 捕獲/捕捉)
			Accept (Ac 朝向 + cept 拿 = 接受)
			Conceive (Con 共同/完全 + ceive 拿 = 構思/懷孕)
			Deceptive (De 錯誤 + cept 拿 = 欺騙性的 —— 誤導你的認知)
		-pel- / -puls- (推/驅使)：
			Expel (Ex 往外 + pel 推 = 開除/驅逐)
			Propel (Pro 向前 + pel 推 = 推進/驅動)
			Compel (Con 加強 + pel 推 = 強迫)
			Impulse (Im 往內 + pulse 推 = 衝動/脈衝)
	「時間與順序」類 
		-chron- (時間)：
			Chronic (Chron 時間 + ic 形容詞尾 = 慢性的/長期的)
			Synchronize (Syn 同時 + chron 時間 + ize 動詞尾 = 同步)
			Chronology (Chron 時間 + ology 學問 = 年表/年代學)
		-temp- (時間/時代)：
			Temporary (Temp 時間 + orary 形容詞尾 = 暫時的)
			Contemporary (Con 共同 + temp 時間 = 當代的/同時代的人)
		-pre- / -fore- (在之前)：
			Preview (Pre 前 + view 看 = 預覽)
			Foresee (Fore 前 + see 看 = 預見)
	「社會、統治與人際」類
		-popul- / -dem- (人民)：
			Population (Popul 人民 + ation 名詞尾 = 人口)
			Democracy (Demo 人民 + cracy 統治 = 民主)
			Epidemic (Epi 在...之間 + dem 人民 = 流行病)
		-reg- / -rect- (管轄/正)：
			Regulate (Reg 管轄 + ulate 動詞尾 = 管理/規範)
			Rectangle (Rect 正/直 + angle 角 = 長方形)
		-soci- (夥伴/群體)：
			Society (Soci 夥伴 + ety 名詞尾 = 社會)
			Associate (As 往 + soci 夥伴 = 聯想/合夥人)
	「自然與科學基礎」類
		-bio- (生命)：
			Biology (Bio 生命 + logy 學問 = 生物學)
			Antibiotic (Anti 反 + bio 生命 = 抗生素)
		-geo- (土地/地球)：
			Geography (Geo 地 + graphy 寫/畫 = 地理)
			Geometry (Geo 地 + metry 測量 = 幾何學)
		-hydro- (水)：
			Hydrant (Hydr 水 + ant 物質 = 消防栓)
			Dehydrate (De 除去 + hydr 水 = 脫水)
	「份量、程度與否定」類
		-magni- / -max- (大)：
			Magnify (Magni 大 + fy 使 = 放大)
			Maximum (Max 最大 + imum = 最大值)
		-min- / -mini- (小)：
			Minimize (Mini 小 + ize 使 = 使最小化)
			Minority (Minor 較小 + ity 名詞尾 = 少數)
		-un- / -in- / -im- / -dis- (否定)：
			Inability (In 不 + ability 能力 = 無能力)
			Disadvantage (Dis 不 + advantage 優勢 = 劣勢)
	「數量與數字」類
		-uni- / -mon- (一)：
			Uniform (Uni 一 + form 形狀 = 統一的/制服)
			Monomial (Mono 單一 + mial 項 = 單項式)
		-bi- / -du- / -di- (二)：
			Binary (Bin 二 + ary = 二進制的)
			Duplicate (Du 二 + plic 摺疊 = 複製/兩份)
			Dilemma (Di 二 + lemma 題目 = 進退兩難)
		-tri- (三)：
			Triangle (Tri 三 + angle 角 = 三角形)
			Trigonometry (Tri 三 + gon 角 + metry 測量 = 三角學)
		-quadr- (四)：
			Quadrant (Quadr 四 + ant = 象限/四分之一圓)
			Quadrilateral (Quadr 四 + latus 邊 = 四邊形)
		-poly- (多)：
			Polygon (Poly 多 + gon 角 = 多邊形)
			Polynomial (Poly 多 + nial 項 = 多項式)
	「形狀、位置與測量」類
		-metr- / -meter- (測量)：
			Symmetry (Sym 共同 + metry 測量 = 對稱)
			Perimeter (Peri 周圍 + meter 測量 = 周長)
			Diameter (Dia 穿過 + meter 測量 = 直徑)
		-gon- (角)：
			Pentagon (Penta 五 + gon 角 = 五邊形)
			Diagonal (Dia 穿過 + gon 角 = 對角線)
		-equ- / -equi- (相等)：
			Equation (Equ 相等 + ation 名詞尾 = 等式/方程式)
			Equivalent (Equi 相等 + valent 價值 = 等值的)
			Equilateral (Equi 相等 + lateral 邊 = 等邊的)
		-fract- / -frag- (打碎/部分)：
			Fraction (Fract 碎片段 = 分數)
			Fragment (Frag 碎塊 = 碎片)
	「邏輯與運算」類
		-log- (比例/推理)：
			Logarithm (Log 比例 + arithm 數字 = 對數)
			Analogy (Ana 根據 + log 比例 = 類比/類推)
		-add- / -sum- (增加/總計)：
			Addition (Add 加 = 加法)
			Summation (Sum 總和 + ation = 加總/求和)
		-multi- (多/增加)：
			Multiply (Multi 多 + ply 摺疊 = 乘法/增加 —— 原意是摺疊多次)
		-vari- (改變)：
			Variable (Vari 改變 + able = 變數)
			Variance (Vari 改變 + ance = 方差/變異數)
		Ac- (Ad-)：往、向、去
			-count- (源自 -comput- / -put-)：計算、思考。
				Accountant (Account + ant 人)：會計師（處理帳務的人）。
				Accountability (Account + ability 能力)：問責制、責任（需要「交代清楚」的能力）。
				Discount (Dis 除去 + count 計算)：折扣（把一部分的計算結果扣掉）。
				Recount (Re 再次 + count 計算)：重新計算、轉述（再次講述一遍故事）。
	「易混對照組」
		拿取 (Take) vs. 頭 (Head)
			-cap- / -cept- (拿/取)：
				Accept (Ac 朝向 + cept 拿 = 接受)
				Capture (Capt 拿 + ure = 捕獲)
			-capit- (頭)：
				Capital (Capit 頭 + al = 首都/資本 —— 最重要的部分)
				Captain (Capit 頭 + ain = 隊長/船長 —— 領頭的人)
				Decapitate (De 除去 + capit 頭 = 斬首)
		伸展 (Stretch) vs. 保持 (Hold)
			-tend- / -tens- (伸展/拉緊)：
				Extend (Ex 出去 + tend 伸 = 延伸/擴展)
				Tension (Tens 拉緊 + ion = 緊張/張力)
			-tain- / -ten- / -tin- (握住/保持)：
				Maintain (Main 手 + tain 握 = 維持)
				Contain (Con 全部 + tain 握 = 包含)
				Continue (Con 全部 + tin 握 = 繼續 —— 一直握著不放)"""

# 執行轉換
final_data = parse_full_etymon_data(raw_data)

# 存成 JSON 檔案
with open('etymon_database.json', 'w', encoding='utf-8') as f:
    json.dump(final_data, f, indent=4, ensure_ascii=False)

print("🎉 轉換成功！已生成 etymon_database.json")