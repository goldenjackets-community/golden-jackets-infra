# Golden Jackets [COUNTRY] — New Chapter Template

## Pre-requisites
- Chapter Leader identified (must be Golden Jacket holder — all 12 AWS certs active)
- Domain registered by Chapter Leader (goldenjackets.[tld])
- LinkedIn Company Page created by Chapter Leader
- Chapter Leader's photo (.png or .jpg, square, min 200x200px)

## Infrastructure Checklist

### AWS Resources (run setup-chapter.sh or manual)
- [ ] Route53 Hosted Zone created
- [ ] S3 Bucket created (website hosting enabled)
- [ ] ACM Certificate requested (domain + www)
- [ ] CloudFront Distribution created
- [ ] DynamoDB Table for visitor counter
- [ ] Lambda function for counter (Function URL)
- [ ] Backup Vault created (daily, 7-day retention)
- [ ] Cognito Group created for chapter

### DNS (Chapter Leader action)
- [ ] Nameservers pointed to Route53 (provided after hosted zone creation)
- [ ] Wait for ACM certificate validation
- [ ] Add custom domain to CloudFront after SSL validates

### GitHub
- [ ] Repository created: goldenjackets-community/golden-jackets-[country]
- [ ] Branch: master
- [ ] deploy.yml workflow configured (S3 sync + CloudFront invalidation + smoke test)
- [ ] Secret CLOUDFRONT_DIST_ID set
- [ ] Chapter Leader added as collaborator (write)

### Lambda Integrations
- [ ] REPO_MAP updated in gj-apply Lambda
- [ ] CORS updated in API Gateway (new domain)
- [ ] IAM policy updated (new S3 bucket)
- [ ] Backup vault added to gj-admin mappings

### Site Customization
- [ ] Country name, flag, domain updated throughout
- [ ] Map SVG with real geographic state/region paths (NOT geometric shapes)
  - Use a public SVG source with real boundaries (e.g. SimpleMaps, Natural Earth, GitHub repos)
  - Add `data-state="XX"` to each path for filtering
  - Highlight the Chapter Leader's state with `class="active"`
  - Add state code labels (`<text>` elements) centered on each state
  - Remove inline fills — let CSS theme control colors via `#[country]-map path` rules
  - Set `pointer-events:none` on text labels
- [ ] Chapter Leader card as member #1
- [ ] States/regions dropdown in filter and apply form
- [ ] Sponsor tiers in local currency
- [ ] Privacy Policy page (local data protection law)
- [ ] Events section with local AWS events
- [ ] Counter Lambda URL updated in footer

### Communication
- [ ] LinkedIn Company Page live
- [ ] Chapter Leader Guide sent
- [ ] Announcement post drafted (wait for Chapter Leader OK)
- [ ] Global site updated (pin, flight path, card, stats)
- [ ] SNS notification configured for new applications

## Site Structure
```
golden-jackets-[country]/
├── index.html          # Main site (single page)
├── members.html        # Members Lounge (Cognito auth)
├── admin.html          # Admin Console
├── privacy.html        # Privacy Policy
├── favicon.ico
├── sitemap.xml
├── robots.txt
├── assets/
│   ├── jacket-[country].png    # Jacket with country flag
│   ├── geriesabouayash.jpg     # Creator photo
│   ├── tutorialsdojo-logo.png  # Partner logo
│   ├── og-image.png            # Open Graph image
│   ├── badges/                 # AWS cert badges
│   ├── members/                # Member photos
│   └── partners/               # Partner logos
└── .github/
    └── workflows/
        └── deploy.yml          # CI/CD pipeline
```

## Naming Conventions
- Bucket: goldenjackets.[tld]
- CloudFront: auto-generated ID
- DynamoDB: gj-[country]-visitors
- Lambda: gj-[country]-counter
- Backup Vault: gj-[country]-backups
- Cognito Group: [country]
- Route53 Zone: goldenjackets.[tld]

## Timeline (typical)
| Day | Action |
|-----|--------|
| 1 | Infra created (setup-chapter.sh) |
| 1 | Nameservers sent to Chapter Leader |
| 1-3 | DNS propagation + SSL validation |
| 2-3 | Site customized and deployed |
| 3 | Custom domain added to CloudFront |
| 3 | Chapter Leader tests admin panel |
| 4-7 | Announcement (when Chapter Leader is ready) |

## Reference
- Setup script: `golden-jackets-infra/new-chapter/setup-chapter.sh`
- Runbook: `golden-jackets-infra/new-chapter/RUNBOOK.md`
- Chapter Leader Guide: `golden-jackets-infra/CHAPTER_LEADER_GUIDE.md`
- AWS Account: 800712212925 (profile: gj)
- Cognito Pool: us-east-1_Z0VzzrmIX
- API: https://kqiq2bltjd.execute-api.us-east-1.amazonaws.com/admin
