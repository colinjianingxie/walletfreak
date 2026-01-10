/**
 * Wallet Card Preview Logic
 */

let selectedAddCard = null;

function resetCardPreview() {
    selectedAddCard = null;
    if (document.getElementById('card-preview-empty')) {
        document.getElementById('card-preview-empty').style.display = 'block';
    }
    if (document.getElementById('card-preview-content')) {
        document.getElementById('card-preview-content').style.display = 'none';
    }
    document.querySelectorAll('.card-result-item').forEach(el => el.classList.remove('selected'));
}

function selectCardForPreview(card, element) {
    // Highlight selection
    document.querySelectorAll('.card-result-item').forEach(el => el.classList.remove('selected'));
    if (element) {
        element.classList.add('selected');
    }

    selectedAddCard = card;

    // Update Preview
    document.getElementById('card-preview-empty').style.display = 'none';
    document.getElementById('card-preview-content').style.display = 'block';

    // Visual
    const visual = document.getElementById('preview-card-visual');
    visual.innerHTML = ''; // Clear previous content
    visual.style.background = 'transparent';
    visual.style.padding = '0';
    visual.style.boxShadow = 'none';

    // Create image
    const img = document.createElement('img');
    img.src = card.image_url || '/static/images/card_placeholder.png'; // Fallback
    img.style.width = '100%';
    img.style.height = 'auto';
    img.style.borderRadius = '12px';
    img.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
    img.alt = card.name;

    visual.appendChild(img);

    // Render Earning Rates
    const earningContainer = document.getElementById('preview-earning-rates');
    if (earningContainer) {
        try {
            earningContainer.innerHTML = '';

            let earning = card.earning_rates || card.earning || card.rewards_structure || [];
            if (!Array.isArray(earning)) earning = [];

            // Fallback to benefits
            if (earning.length === 0) {
                const benefits = card.benefits || [];
                if (Array.isArray(benefits)) {
                    earning = benefits.filter(b => b && (b.benefit_type === 'Multiplier' || b.benefit_type === 'Cashback')).map(b => ({
                        category: b.short_description || b.name || b.title || b.description,
                        rate: b.numeric_value || b.value || b.multiplier,
                        currency: b.benefit_type === 'Cashback' ? 'cash' : (b.currency || 'points'),
                        details: b.description || b.long_description || b.additional_details
                    }));
                }
            }

            // Filter invalid items
            earning = earning.filter(item => item);

            if (earning.length > 0) {
                earning.sort((a, b) => {
                    const rateA = parseFloat(a.rate || a.value || 0);
                    const rateB = parseFloat(b.rate || b.value || 0);
                    return rateB - rateA;
                });

                earning.forEach(item => {
                    // Support different field names
                    let cat = item.category || item.cat || item.description || 'Category';
                    // Handle array categories (new format)
                    if (Array.isArray(cat)) {
                        cat = cat.join(', ');
                    }

                    const rate = parseFloat(item.rate || item.value || item.multiplier || 0);
                    const currency = item.currency || 'points';

                    // Build details text similar to card_modal.html
                    let details = item.details || item.description_long || item.additional_details || '';

                    // Handle array details
                    if (Array.isArray(details)) {
                        details = details.join(', ');
                    }

                    if (!details) {
                        // Generate default details text
                        if ((currency && String(currency).toLowerCase().includes('cash')) || (item.benefit_type === 'Cashback')) {
                            details = `Earn ${rate}% cash back on ${cat.toLowerCase()}.`;
                        } else {
                            details = `Earn ${rate}x ${currency} on ${cat.toLowerCase()}.`;
                        }
                    }

                    // Title Case Helper
                    const toTitleCase = (str) => {
                        if (typeof str !== 'string') return String(str);
                        return str.toLowerCase().split(' ').map(word => {
                            return word.charAt(0).toUpperCase() + word.slice(1);
                        }).join(' ');
                    };

                    const displayTitle = toTitleCase(details);

                    let displayRate;
                    if ((currency && String(currency).toLowerCase().includes('cash')) || (item.benefit_type === 'Cashback') || String(item.rate || '').includes('%')) {
                        // Fix: if rate is raw number, append %. If it's "3%", leave it.
                        // But we parsed float above.
                        // Let's stick to simple logic:
                        if (String(item.rate).includes('%')) displayRate = item.rate;
                        else displayRate = `${rate}%`;
                    } else {
                        displayRate = `${rate}x`;
                    }

                    const row = document.createElement('div');
                    row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; font-size: 0.875rem;';
                    row.innerHTML = `
                        <div style="color: #475569; font-weight: 500;">${displayTitle}</div>
                        <div style="font-weight: 700; color: #0F172A; background: #E0E7FF; color: #4338CA; padding: 0.125rem 0.5rem; border-radius: 4px;">${displayRate}</div>
                    `;
                    earningContainer.appendChild(row);
                });
            } else {
                earningContainer.innerHTML = '<div style="color: #94A3B8; font-size: 0.875rem; font-style: italic;">No earning rates details available.</div>';
            }
        } catch (e) {
            console.error('Error rendering earning rates:', e);
            earningContainer.innerHTML = '<div style="color: #EF4444; font-size: 0.875rem;">Error displaying rates</div>';
        }
    }

    // Render Credits
    const creditsContainer = document.getElementById('preview-credits');
    if (creditsContainer) {
        try {
            creditsContainer.innerHTML = '';

            const benefits = card.benefits || [];
            let filteredBenefits = [];
            if (Array.isArray(benefits)) {
                filteredBenefits = benefits.filter(b => b && b.benefit_type !== 'Multiplier' && b.benefit_type !== 'Cashback');
            }

            // Prioritize explicit credits list if available
            let credits = card.credits;
            if (Array.isArray(credits) && credits.length > 0) {
                // Use credits if available
                filteredBenefits = credits;
            }

            // Filter out Protection and Bonus benefits
            filteredBenefits = filteredBenefits.filter(b => b && b.benefit_type !== 'Protection' && b.benefit_type !== 'Bonus');

            if (filteredBenefits.length > 0) {
                filteredBenefits.forEach((benefit, index) => {
                    if (!benefit) return;

                    const name = benefit.short_description || benefit.name || benefit.title || 'Benefit';
                    const value = benefit.numeric_value || benefit.value || benefit.amount || benefit.dollar_value;
                    let description = benefit.long_description || benefit.description || '';
                    if (benefit.additional_details) {
                        description += (description ? '<br><br>' : '') + benefit.additional_details;
                    }

                    let valueDisplay = String(value);
                    let shouldShow = false;

                    if (value && (typeof value === 'number' || !isNaN(parseFloat(value)))) {
                        if (!valueDisplay.includes('$')) valueDisplay = '$' + valueDisplay;
                        shouldShow = true;
                    } else if (String(value).toLowerCase() === 'included') {
                        valueDisplay = 'Included';
                        shouldShow = true;
                    }

                    // Always show if it's explicitly in 'credits' list, otherwise check value
                    if (shouldShow) {
                        const uniqueId = `preview-credit-${card.id}-${index}`;

                        const row = document.createElement('div');
                        row.onclick = () => {
                            const descEl = document.getElementById(uniqueId);
                            if (descEl) descEl.style.display = descEl.style.display === 'none' ? 'block' : 'none';
                            const icon = document.getElementById(`icon-${uniqueId}`);
                            if (icon) icon.style.transform = icon.style.transform === 'rotate(90deg)' ? 'rotate(0deg)' : 'rotate(90deg)';
                        };
                        row.style.cursor = 'pointer';

                        row.innerHTML = `
                            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.875rem 0; border-bottom: 1px solid #F3F4F6;">
                                <div style="font-weight: 500; color: #1F2937; font-size: 0.95rem; max-width: 65%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${name}</div>
                                <div style="display: flex; align-items: center; gap: 0.75rem;">
                                    <div style="color: #6366F1; font-weight: 700; font-size: 0.95rem;">${valueDisplay}</div>
                                    <span id="icon-${uniqueId}" class="material-icons" style="font-size: 18px; color: #D1D5DB; transition: transform 0.2s;">chevron_right</span>
                                </div>
                            </div>
                            <div id="${uniqueId}" style="display: none; padding: 0 0 1rem 0; color: #64748B; font-size: 0.9rem; line-height: 1.5; border-bottom: 1px solid #F3F4F6;">
                                ${description || 'No description available'}
                            </div>
                        `;
                        creditsContainer.appendChild(row);
                    }
                });
            }

            if (creditsContainer.children.length === 0) {
                creditsContainer.innerHTML = '<div style="color: #94A3B8; font-size: 0.875rem; font-style: italic;">No credits available</div>';
            }
        } catch (e) {
            console.error('Error rendering credits:', e);
            creditsContainer.innerHTML = '<div style="color: #EF4444; font-size: 0.875rem;">Error displaying credits</div>';
        }
    }
}
