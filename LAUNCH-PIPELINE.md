# NameCraft Launch Pipeline

> First product through the 48nauts pipeline

**Status:** 🟡 In Progress
**Target:** Live with payments THIS WEEK

---

## Pipeline Tasks

### Phase 1: Prerequisites (Andre)
- [ ] **Pick domain** — `namecraft.io` or `namecraft.ai`?
- [ ] **Sign up for Paddle** — https://paddle.com (use DAT.AG or 21nauts entity)
- [ ] **Decide pricing** — Suggested: $19/mo Pro, $49/mo Business

### Phase 2: Paddle Setup (Jarvis)
- [ ] Create product in Paddle dashboard
- [ ] Set up Pro tier ($19/mo subscription)
- [ ] Set up Business tier ($49/mo subscription)  
- [ ] Get checkout embed code
- [ ] Configure webhooks for license validation

### Phase 3: Landing Page (Jarvis)
- [ ] Write landing page copy
- [ ] Add pricing section with Paddle checkout buttons
- [ ] Add features comparison (Free vs Pro vs Business)
- [ ] Mobile responsive check
- [ ] Add social proof section (placeholder for now)

### Phase 4: Deploy (Jarvis)
- [ ] Create Coolify app
- [ ] Configure domain + SSL
- [ ] Set environment variables
- [ ] Deploy and test checkout flow
- [ ] Verify Paddle webhooks working

### Phase 5: Launch (Jarvis + Andre)
- [ ] Soft launch — share link with a few people
- [ ] Fix any issues
- [ ] Write launch tweet thread
- [ ] Post on Twitter (@andrewolke, @21nauts)
- [ ] Submit to Product Hunt (optional)

---

## Paddle Setup Guide

### Step 1: Sign Up
1. Go to https://paddle.com
2. Sign up with business email
3. Complete verification (may take 1-2 days)

### Step 2: Create Product
1. Dashboard → Catalog → Products → New Product
2. Name: "NameCraft Pro"
3. Tax category: "SaaS" (needs verification first time)
4. Add description and icon

### Step 3: Create Prices
```
Pro Tier:
- $19/month (or €19)
- Recurring monthly

Business Tier:
- $49/month (or €49)
- Recurring monthly
```

### Step 4: Get Checkout Code
Paddle overlay checkout (simplest):
```html
<script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
<script>
  Paddle.Initialize({ token: 'YOUR_CLIENT_TOKEN' });
</script>

<button onclick="Paddle.Checkout.open({
  items: [{ priceId: 'pri_xxxxx', quantity: 1 }]
})">
  Get Pro - $19/mo
</button>
```

### Step 5: Webhooks
Set up webhook endpoint to:
- Create user account on successful payment
- Generate API key / license
- Handle cancellations

---

## Pricing Strategy

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | Algorithmic generation, basic domain check |
| **Pro** | $19/mo | AI Smart Filter, deep validation, favorites sync, API (100 req/day) |
| **Business** | $49/mo | Team workspaces, API (unlimited), white-label, priority support |

---

## Domain Options

| Domain | Available? | Price | Notes |
|--------|------------|-------|-------|
| namecraft.io | Check | ~$50/yr | Clean, professional |
| namecraft.ai | Check | ~$80/yr | AI-focused, premium |
| namecraft.app | Check | ~$15/yr | Budget option |
| getnamecraft.com | Check | ~$12/yr | Fallback |

---

## Timeline

| Day | Task |
|-----|------|
| Today | Andre: Domain + Paddle signup |
| Day 1-2 | Jarvis: Paddle products + landing page |
| Day 2-3 | Jarvis: Deploy to Coolify |
| Day 3 | Soft launch, test payments |
| Day 4 | Public launch tweet |

---

*First product through 48nauts pipeline. Let's ship it.*
