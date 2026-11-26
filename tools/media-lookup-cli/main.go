package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const userAgent = "media-lookup-cli/1.0 (+https://github.com/Mostakim2005/database-manager)"

var httpClient = &http.Client{Timeout: 15 * time.Second}

type MappingFiles struct {
	Dir               string `json:"dir"`
	AnimeOfflineDB    string `json:"anime_offline_db"`
	FribbList         string `json:"fribb_anime_list"`
	AnibridgeMappings string `json:"anibridge_mappings"`
	RensetsuBangumi   string `json:"rensetsu_bangumi"`
	RensetsuSilver    string `json:"rensetsu_silveryasha"`
}

func resolveMappingsDir(override string) string {
	if override != "" {
		return override
	}
	if env := os.Getenv("MEDIA_MAPPINGS_DIR"); env != "" {
		return env
	}
	if localApp := os.Getenv("LOCALAPPDATA"); localApp != "" {
		cand := filepath.Join(localApp, "SharedLibraries", "media-mappings")
		if st, err := os.Stat(cand); err == nil && st.IsDir() {
			return cand
		}
	}
	home, _ := os.UserHomeDir()
	regPath := filepath.Join(home, ".local", "share", "ecosystem-registry.json")
	if b, err := os.ReadFile(regPath); err == nil {
		var reg struct {
			Paths map[string]string `json:"paths"`
		}
		if json.Unmarshal(b, &reg) == nil {
			if cl := reg.Paths["commonLibraries"]; cl != "" {
				return filepath.Join(cl, "media-mappings")
			}
		}
	}
	return filepath.Join(home, "AppData", "Local", "SharedLibraries", "media-mappings")
}

func getMappingFiles(dir string) MappingFiles {
	return MappingFiles{
		Dir:               dir,
		AnimeOfflineDB:    filepath.Join(dir, "anime-offline-database-minified.json"),
		FribbList:         filepath.Join(dir, "fribb-anime-list-full.json"),
		AnibridgeMappings: filepath.Join(dir, "anibridge-mappings.min.json"),
		RensetsuBangumi:   filepath.Join(dir, "rensetsu-bangumi.min.json"),
		RensetsuSilver:    filepath.Join(dir, "rensetsu-silveryasha.min.json"),
	}
}

func emitJSON(v any) {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	enc.SetEscapeHTML(false)
	_ = enc.Encode(v)
}

func fatalJSON(msg string) {
	emitJSON(map[string]any{"ok": false, "error": msg})
	os.Exit(1)
}

func httpJSON(method, target string, body any, extraHeaders map[string]string) ([]byte, error) {
	var bodyReader io.Reader
	if body != nil {
		raw, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		bodyReader = bytes.NewReader(raw)
	}
	req, err := http.NewRequest(method, target, bodyReader)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept", "application/json")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	for k, v := range extraHeaders {
		req.Header.Set(k, v)
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if err != nil {
		return nil, err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return data, fmt.Errorf("HTTP %d from %s", resp.StatusCode, target)
	}
	return data, nil
}

// --- Offline Mapping Structures ---

type FribbEntry struct {
	Type        string   `json:"type"`
	AniDBID     int      `json:"anidb_id"`
	AniListID   int      `json:"anilist_id"`
	MALID       int      `json:"mal_id"`
	KitsuID     int      `json:"kitsu_id"`
	TVDBID      int      `json:"tvdb_id"`
	IMDBID      any      `json:"imdb_id"`
	TMDB        any      `json:"themoviedb_id"`
	LiveChartID int      `json:"livechart_id"`
	AnimePlanet string   `json:"anime-planet_id"`
}

type AODBEntry struct {
	Sources      []string `json:"sources"`
	Title        string   `json:"title"`
	Type         string   `json:"type"`
	Episodes     int      `json:"episodes"`
	Status       string   `json:"status"`
	AnimeSeason  struct {
		Season string `json:"season"`
		Year   int    `json:"year"`
	} `json:"animeSeason"`
	Picture      string   `json:"picture"`
	Thumbnail    string   `json:"thumbnail"`
	Synonyms     []string `json:"synonyms"`
	RelatedAnime []string `json:"relatedAnime"`
}

type AODBRoot struct {
	Data []AODBEntry `json:"data"`
}

type RensetsuEntry struct {
	UUID         string         `json:"uuid"`
	TitleDisplay string         `json:"title_display"`
	TitleNative  string         `json:"title_native"`
	TitleEnglish string         `json:"title_english"`
	Synonyms     []string       `json:"synonyms"`
	MediaType    string         `json:"media_type"`
	Year         int            `json:"year"`
	Country      string         `json:"country_of_origin"`
	Mappings     map[string]any `json:"mappings"`
}

var sourceIDRe = regexp.MustCompile(`(anilist\.co/anime|myanimelist\.net/anime|kitsu\.(?:app|io)/anime|anidb\.net/anime)/(\d+)`)

func parseAODBSources(sources []string) map[string]int {
	out := map[string]int{}
	for _, s := range sources {
		m := sourceIDRe.FindStringSubmatch(s)
		if len(m) == 3 {
			id, _ := strconv.Atoi(m[2])
			if id <= 0 {
				continue
			}
			switch {
			case strings.Contains(m[1], "anilist"):
				out["anilist_id"] = id
			case strings.Contains(m[1], "myanimelist"):
				out["mal_id"] = id
			case strings.Contains(m[1], "kitsu"):
				out["kitsu_id"] = id
			case strings.Contains(m[1], "anidb"):
				out["anidb_id"] = id
			}
		}
	}
	return out
}

func normalizeKey(s string) string {
	s = strings.ToLower(strings.TrimSpace(s))
	var b strings.Builder
	lastSpace := false
	for _, r := range s {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r > 127 {
			b.WriteRune(r)
			lastSpace = false
		} else if !lastSpace {
			b.WriteByte(' ')
			lastSpace = true
		}
	}
	return strings.TrimSpace(b.String())
}

func titleMatches(query string, candidates ...string) bool {
	qn := normalizeKey(query)
	if qn == "" {
		return false
	}
	for _, c := range candidates {
		cn := normalizeKey(c)
		if cn == "" {
			continue
		}
		if cn == qn || strings.Contains(cn, qn) {
			return true
		}
	}
	return false
}

// --- AniList GraphQL ---

type AniListMedia struct {
	ID          int      `json:"id"`
	IDMAL       *int     `json:"idMal"`
	Type        string   `json:"type"`
	Format      string   `json:"format"`
	Status      string   `json:"status"`
	Episodes    *int     `json:"episodes"`
	Chapters    *int     `json:"chapters"`
	IsAdult     bool     `json:"isAdult"`
	SiteURL     string   `json:"siteUrl"`
	Synonyms    []string `json:"synonyms"`
	Description string   `json:"description"`
	StartDate   struct {
		Year *int `json:"year"`
	} `json:"startDate"`
	Title struct {
		English string `json:"english"`
		Romaji  string `json:"romaji"`
		Native  string `json:"native"`
	} `json:"title"`
	CoverImage struct {
		ExtraLarge string `json:"extraLarge"`
		Large      string `json:"large"`
		Medium     string `json:"medium"`
	} `json:"coverImage"`
	ExternalLinks []struct {
		Site string `json:"site"`
		URL  string `json:"url"`
	} `json:"externalLinks"`
	Relations struct {
		Edges []struct {
			RelationType string `json:"relationType"`
			Node         struct {
				ID        int    `json:"id"`
				IDMAL     *int   `json:"idMal"`
				Type      string `json:"type"`
				Format    string `json:"format"`
				Status    string `json:"status"`
				Episodes  *int   `json:"episodes"`
				SiteURL   string `json:"siteUrl"`
				StartDate struct {
					Year *int `json:"year"`
				} `json:"startDate"`
				Title struct {
					English string `json:"english"`
					Romaji  string `json:"romaji"`
					Native  string `json:"native"`
				} `json:"title"`
				CoverImage struct {
					Large string `json:"large"`
				} `json:"coverImage"`
			} `json:"node"`
		} `json:"edges"`
	} `json:"relations"`
}

func queryAniListSearch(query, mediaType string, limit int) ([]AniListMedia, error) {
	var typeFilter string
	switch strings.ToUpper(mediaType) {
	case "ANIME", "DONGHUA":
		typeFilter = ", type: ANIME"
	case "MANGA", "COMIC", "NOVEL":
		typeFilter = ", type: MANGA"
	}
	gql := fmt.Sprintf(`query ($s: String, $perPage: Int) {
  Page(perPage: $perPage) {
    media(search: $s%s) {
      id idMal type format status episodes chapters isAdult siteUrl synonyms description(asHtml: false)
      startDate { year }
      title { english romaji native }
      coverImage { extraLarge large medium }
      externalLinks { site url }
      relations {
        edges {
          relationType
          node {
            id idMal type format status episodes siteUrl
            startDate { year }
            title { english romaji native }
            coverImage { large }
          }
        }
      }
    }
  }
}`, typeFilter)

	raw, err := httpJSON("POST", "https://graphql.anilist.co", map[string]any{
		"query":     gql,
		"variables": map[string]any{"s": query, "perPage": limit},
	}, nil)
	if err != nil {
		return nil, err
	}
	var resp struct {
		Data struct {
			Page struct {
				Media []AniListMedia `json:"media"`
			} `json:"page"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &resp); err != nil {
		return nil, err
	}
	return resp.Data.Page.Media, nil
}

func queryAniListByID(id int) (*AniListMedia, error) {
	gql := `query ($id: Int) {
  Media(id: $id) {
    id idMal type format status episodes chapters isAdult siteUrl synonyms description(asHtml: false)
    startDate { year }
    title { english romaji native }
    coverImage { extraLarge large medium }
    externalLinks { site url }
    relations {
      edges {
        relationType
        node {
          id idMal type format status episodes siteUrl
          startDate { year }
          title { english romaji native }
          coverImage { large }
        }
      }
    }
  }
}`
	raw, err := httpJSON("POST", "https://graphql.anilist.co", map[string]any{
		"query":     gql,
		"variables": map[string]any{"id": id},
	}, nil)
	if err != nil {
		return nil, err
	}
	var resp struct {
		Data struct {
			Media *AniListMedia `json:"Media"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &resp); err != nil {
		return nil, err
	}
	return resp.Data.Media, nil
}

func queryIMDbSuggestion(query string) ([]map[string]any, error) {
	qn := normalizeKey(query)
	if qn == "" {
		return nil, nil
	}
	first := "a"
	for _, r := range qn {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') {
			first = string(r)
			break
		}
	}
	target := fmt.Sprintf("https://v3.sg.media-imdb.com/suggestion/%s/%s.json", first, url.PathEscape(query))
	raw, err := httpJSON("GET", target, nil, nil)
	if err != nil {
		return nil, err
	}
	var payload struct {
		D []map[string]any `json:"d"`
	}
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, err
	}
	var hits []map[string]any
	for _, item := range payload.D {
		id, _ := item["id"].(string)
		if !strings.HasPrefix(id, "tt") {
			continue
		}
		poster := ""
		if imgObj, ok := item["i"].(map[string]any); ok {
			poster, _ = imgObj["imageUrl"].(string)
		}
		hits = append(hits, map[string]any{
			"imdb_id":    id,
			"title":      item["l"],
			"year":       item["y"],
			"kind":       item["q"],
			"cast":       item["s"],
			"imdb_url":   fmt.Sprintf("https://www.imdb.com/title/%s/", id),
			"poster_url": poster,
		})
		if len(hits) >= 5 {
			break
		}
	}
	return hits, nil
}

func queryBangumiSearch(query string, subjectType int) ([]map[string]any, error) {
	target := fmt.Sprintf("https://api.bgm.tv/search/subject/%s?type=%d&responseGroup=small&max_results=5", url.PathEscape(query), subjectType)
	raw, err := httpJSON("GET", target, nil, nil)
	if err != nil {
		return nil, err
	}
	var payload struct {
		List []map[string]any `json:"list"`
	}
	if err := json.Unmarshal(raw, &payload); err != nil {
		return nil, err
	}
	var hits []map[string]any
	for _, row := range payload.List {
		poster := ""
		if imgs, ok := row["images"].(map[string]any); ok {
			for _, k := range []string{"large", "common", "medium"} {
				if u, ok := imgs[k].(string); ok && u != "" {
					poster = strings.Replace(u, "http://", "https://", 1)
					break
				}
			}
		}
		urlStr, _ := row["url"].(string)
		hits = append(hits, map[string]any{
			"bangumi_id": row["id"],
			"name":       row["name"],
			"name_cn":    row["name_cn"],
			"air_date":   row["air_date"],
			"url":        strings.Replace(urlStr, "http://", "https://", 1),
			"poster_url": poster,
		})
	}
	return hits, nil
}

// --- Offline Dataset Lookups ---

func lookupFribb(path string, anilistID, malID int, imdbID string) []FribbEntry {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var rows []FribbEntry
	if json.Unmarshal(b, &rows) != nil {
		return nil
	}
	var matches []FribbEntry
	for _, r := range rows {
		if anilistID > 0 && r.AniListID == anilistID {
			matches = append(matches, r)
			continue
		}
		if malID > 0 && r.MALID == malID {
			matches = append(matches, r)
			continue
		}
		if imdbID != "" {
			raw, _ := json.Marshal(r.IMDBID)
			if strings.Contains(strings.ToLower(string(raw)), strings.ToLower(imdbID)) {
				matches = append(matches, r)
			}
		}
	}
	return matches
}

func lookupAODB(path string, anilistID, malID int, title string, limit int) []map[string]any {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var root AODBRoot
	if json.Unmarshal(b, &root) != nil {
		return nil
	}
	var out []map[string]any
	for _, e := range root.Data {
		ids := parseAODBSources(e.Sources)
		matched := false
		if anilistID > 0 && ids["anilist_id"] == anilistID {
			matched = true
		} else if malID > 0 && ids["mal_id"] == malID {
			matched = true
		} else if title != "" {
			cands := append([]string{e.Title}, e.Synonyms...)
			matched = titleMatches(title, cands...)
		}
		if matched {
			out = append(out, map[string]any{
				"title":         e.Title,
				"type":          e.Type,
				"episodes":      e.Episodes,
				"status":        e.Status,
				"year":          e.AnimeSeason.Year,
				"season":        e.AnimeSeason.Season,
				"poster_url":    e.Picture,
				"thumbnail_url": e.Thumbnail,
				"ids":           ids,
				"sources":       e.Sources,
				"related_anime": e.RelatedAnime,
				"synonyms":      e.Synonyms,
			})
			if limit > 0 && len(out) >= limit {
				break
			}
		}
	}
	return out
}

func lookupRensetsu(path string, bangumiID int, title string, limit int) []RensetsuEntry {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var rows []RensetsuEntry
	if json.Unmarshal(b, &rows) != nil {
		return nil
	}
	var out []RensetsuEntry
	for _, r := range rows {
		matched := false
		if bangumiID > 0 {
			if rawID, ok := r.Mappings["bangumi"]; ok {
				if fmt.Sprintf("%v", rawID) == strconv.Itoa(bangumiID) {
					matched = true
				}
			}
		}
		if !matched && title != "" {
			cands := append([]string{r.TitleDisplay, r.TitleNative, r.TitleEnglish}, r.Synonyms...)
			matched = titleMatches(title, cands...)
		}
		if matched {
			out = append(out, r)
			if limit > 0 && len(out) >= limit {
				break
			}
		}
	}
	return out
}

func lookupAnibridge(path string, anilistID, malID int) []map[string]any {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	var root map[string]any
	if json.Unmarshal(b, &root) != nil {
		return nil
	}
	alNeedle := ""
	malNeedle := ""
	if anilistID > 0 {
		alNeedle = fmt.Sprintf("anilist:%d", anilistID)
	}
	if malID > 0 {
		malNeedle = fmt.Sprintf("mal:%d", malID)
	}
	var out []map[string]any
	for k, v := range root {
		if k == "$meta" {
			continue
		}
		m, ok := v.(map[string]any)
		if !ok {
			continue
		}
		_, hasAL := m[alNeedle]
		_, hasMAL := m[malNeedle]
		if (alNeedle != "" && (k == alNeedle || hasAL)) || (malNeedle != "" && (k == malNeedle || hasMAL)) {
			out = append(out, map[string]any{"key": k, "mappings": m})
			if len(out) >= 10 {
				break
			}
		}
	}
	return out
}

func bestPoster(m *AniListMedia) string {
	if m == nil {
		return ""
	}
	if m.CoverImage.ExtraLarge != "" {
		return m.CoverImage.ExtraLarge
	}
	if m.CoverImage.Large != "" {
		return m.CoverImage.Large
	}
	return m.CoverImage.Medium
}

// --- Subcommands ---

func cmdStatus(mappingsDir string) {
	mf := getMappingFiles(mappingsDir)
	files := map[string]string{
		"anime_offline_db":     mf.AnimeOfflineDB,
		"fribb_anime_list":     mf.FribbList,
		"anibridge_mappings":   mf.AnibridgeMappings,
		"rensetsu_bangumi":     mf.RensetsuBangumi,
		"rensetsu_silveryasha": mf.RensetsuSilver,
	}
	info := map[string]any{}
	allOK := true
	for name, p := range files {
		st, err := os.Stat(p)
		if err != nil {
			allOK = false
			info[name] = map[string]any{"exists": false, "path": p}
		} else {
			info[name] = map[string]any{"exists": true, "path": p, "bytes": st.Size()}
		}
	}
	emitJSON(map[string]any{"ok": allOK, "mappings_dir": mappingsDir, "datasets": info})
}

func cmdSearch(args []string, mappingsDir string) {
	fs := flag.NewFlagSet("search", flag.ExitOnError)
	query := fs.String("query", "", "Title to search")
	mediaType := fs.String("type", "all", "all | anime | manga")
	limit := fs.Int("limit", 5, "Max results per source")
	includeIMDb := fs.Bool("imdb", false, "Also query IMDb suggestion JSON")
	includeBangumi := fs.Bool("bangumi", false, "Also query Bangumi REST API")
	offlineOnly := fs.Bool("offline", false, "Search offline SharedLibraries datasets only")
	_ = fs.Parse(args)

	if strings.TrimSpace(*query) == "" {
		fatalJSON("--query is required")
	}

	mf := getMappingFiles(mappingsDir)
	resp := map[string]any{
		"ok":    true,
		"query": *query,
		"type":  *mediaType,
	}

	if !*offlineOnly {
		al, err := queryAniListSearch(*query, *mediaType, *limit)
		if err != nil {
			resp["anilist_error"] = err.Error()
		} else {
			resp["anilist"] = al
		}
		if *includeIMDb {
			imdbHits, err := queryIMDbSuggestion(*query)
			if err != nil {
				resp["imdb_error"] = err.Error()
			} else {
				resp["imdb"] = imdbHits
			}
		}
		if *includeBangumi {
			subj := 2
			if strings.EqualFold(*mediaType, "manga") {
				subj = 1
			}
			bgmHits, err := queryBangumiSearch(*query, subj)
			if err != nil {
				resp["bangumi_error"] = err.Error()
			} else {
				resp["bangumi"] = bgmHits
			}
		}
	}

	resp["offline_aodb"] = lookupAODB(mf.AnimeOfflineDB, 0, 0, *query, *limit)
	resp["offline_rensetsu_bangumi"] = lookupRensetsu(mf.RensetsuBangumi, 0, *query, *limit)
	emitJSON(resp)
}

func cmdResolve(args []string, mappingsDir string) {
	fs := flag.NewFlagSet("resolve", flag.ExitOnError)
	anilistID := fs.Int("anilist-id", 0, "AniList media ID")
	malID := fs.Int("mal-id", 0, "MyAnimeList ID")
	bangumiID := fs.Int("bangumi-id", 0, "Bangumi subject ID")
	imdbID := fs.String("imdb-id", "", "IMDb ID (e.g. tt10827146)")
	title := fs.String("title", "", "Optional title filter")
	_ = fs.Parse(args)

	if *anilistID == 0 && *malID == 0 && *bangumiID == 0 && *imdbID == "" && *title == "" {
		fatalJSON("provide --anilist-id, --mal-id, --bangumi-id, --imdb-id, or --title")
	}

	mf := getMappingFiles(mappingsDir)
	fribb := lookupFribb(mf.FribbList, *anilistID, *malID, *imdbID)
	aodb := lookupAODB(mf.AnimeOfflineDB, *anilistID, *malID, *title, 5)
	anibridge := lookupAnibridge(mf.AnibridgeMappings, *anilistID, *malID)
	renBgm := lookupRensetsu(mf.RensetsuBangumi, *bangumiID, *title, 5)
	renSilver := lookupRensetsu(mf.RensetsuSilver, *bangumiID, *title, 5)

	emitJSON(map[string]any{
		"ok":                   true,
		"anilist_id":           *anilistID,
		"mal_id":               *malID,
		"bangumi_id":           *bangumiID,
		"imdb_id":              *imdbID,
		"fribb":                fribb,
		"anibridge":            anibridge,
		"anime_offline_db":     aodb,
		"rensetsu_bangumi":     renBgm,
		"rensetsu_silveryasha": renSilver,
	})
}

func cmdDiscover(args []string, mappingsDir string) {
	fs := flag.NewFlagSet("discover", flag.ExitOnError)
	anilistID := fs.Int("anilist-id", 0, "AniList media ID")
	title := fs.String("title", "", "Title to search if --anilist-id omitted")
	mediaType := fs.String("type", "anime", "all | anime | manga")
	_ = fs.Parse(args)

	var target *AniListMedia
	var err error
	if *anilistID > 0 {
		target, err = queryAniListByID(*anilistID)
	} else if strings.TrimSpace(*title) != "" {
		hits, sErr := queryAniListSearch(*title, *mediaType, 1)
		err = sErr
		if len(hits) > 0 {
			target = &hits[0]
		}
	} else {
		fatalJSON("provide --anilist-id or --title")
	}
	if err != nil {
		fatalJSON(err.Error())
	}
	if target == nil {
		fatalJSON("no AniList match found")
	}

	var related []map[string]any
	for _, edge := range target.Relations.Edges {
		n := edge.Node
		related = append(related, map[string]any{
			"relation_type": edge.RelationType,
			"anilist_id":    n.ID,
			"mal_id":        n.IDMAL,
			"type":          n.Type,
			"format":        n.Format,
			"status":        n.Status,
			"episodes":      n.Episodes,
			"year":          n.StartDate.Year,
			"title_english": n.Title.English,
			"title_romaji":  n.Title.Romaji,
			"title_native":  n.Title.Native,
			"poster_url":    n.CoverImage.Large,
			"site_url":      n.SiteURL,
		})
	}

	mf := getMappingFiles(mappingsDir)
	aodb := lookupAODB(mf.AnimeOfflineDB, target.ID, 0, "", 1)

	emitJSON(map[string]any{
		"ok":               true,
		"anilist_id":       target.ID,
		"title":            target.Title,
		"format":           target.Format,
		"year":             target.StartDate.Year,
		"poster_url":       bestPoster(target),
		"site_url":         target.SiteURL,
		"anilist_relations": related,
		"aodb_match":       aodb,
	})
}

func cmdPoster(args []string, mappingsDir string) {
	fs := flag.NewFlagSet("poster", flag.ExitOnError)
	title := fs.String("title", "", "Title to look up")
	mediaType := fs.String("type", "all", "all | anime | manga")
	outPath := fs.String("out", "", "Optional output file path to download poster")
	_ = fs.Parse(args)

	if strings.TrimSpace(*title) == "" {
		fatalJSON("--title is required")
	}

	posterURL := ""
	source := ""
	al, err := queryAniListSearch(*title, *mediaType, 1)
	if err == nil && len(al) > 0 {
		posterURL = bestPoster(&al[0])
		if posterURL != "" {
			source = "anilist"
		}
	}
	if posterURL == "" {
		mf := getMappingFiles(mappingsDir)
		aodb := lookupAODB(mf.AnimeOfflineDB, 0, 0, *title, 1)
		if len(aodb) > 0 {
			if p, ok := aodb[0]["poster_url"].(string); ok && p != "" {
				posterURL = p
				source = "anime_offline_db"
			}
		}
	}
	if posterURL == "" {
		if bgm, bErr := queryBangumiSearch(*title, 2); bErr == nil && len(bgm) > 0 {
			if p, ok := bgm[0]["poster_url"].(string); ok && p != "" {
				posterURL = p
				source = "bangumi"
			}
		}
	}
	if posterURL == "" {
		if imdb, iErr := queryIMDbSuggestion(*title); iErr == nil && len(imdb) > 0 {
			if p, ok := imdb[0]["poster_url"].(string); ok && p != "" {
				posterURL = p
				source = "imdb"
			}
		}
	}

	saved := ""
	if posterURL != "" && *outPath != "" {
		req, _ := http.NewRequest("GET", posterURL, nil)
		req.Header.Set("User-Agent", userAgent)
		resp, dErr := httpClient.Do(req)
		if dErr == nil {
			defer resp.Body.Close()
			if resp.StatusCode >= 200 && resp.StatusCode < 300 {
				if data, rErr := io.ReadAll(io.LimitReader(resp.Body, 10<<20)); rErr == nil {
					_ = os.MkdirAll(filepath.Dir(*outPath), 0o755)
					if os.WriteFile(*outPath, data, 0o644) == nil {
						saved = *outPath
					}
				}
			}
		}
	}

	emitJSON(map[string]any{
		"ok":         posterURL != "",
		"title":      *title,
		"source":     source,
		"poster_url": posterURL,
		"saved_file": saved,
	})
}

func main() {
	if len(os.Args) < 2 {
		emitJSON(map[string]any{
			"ok":          false,
			"usage":       "media-lookup [--mappings-dir DIR] <status|search|resolve|discover|poster> [flags]",
			"subcommands": []string{"status", "search", "resolve", "discover", "poster"},
		})
		os.Exit(1)
	}

	idx := 1
	mappingsOverride := ""
	if os.Args[1] == "--mappings-dir" && len(os.Args) >= 4 {
		mappingsOverride = os.Args[2]
		idx = 3
	}
	mappingsDir := resolveMappingsDir(mappingsOverride)
	sub := os.Args[idx]
	rest := os.Args[idx+1:]

	switch sub {
	case "status":
		cmdStatus(mappingsDir)
	case "search":
		cmdSearch(rest, mappingsDir)
	case "resolve":
		cmdResolve(rest, mappingsDir)
	case "discover":
		cmdDiscover(rest, mappingsDir)
	case "poster":
		cmdPoster(rest, mappingsDir)
	default:
		fatalJSON("unknown subcommand: " + sub)
	}
}
