const form = document.getElementById('shortenerForm');
const originalUrlInput = document.getElementById('originalUrl');
const customAliasInput = document.getElementById('customAlias');
const shortenedUrlInput = document.getElementById('shortenedUrl');
const shortenedUrlLink = document.getElementById('shortenedUrlLink');
const copyButton = document.getElementById('copyButton');
const submitButton = document.getElementById('submitButton');
const statusMessage = document.getElementById('statusMessage');
const originalUrlError = document.getElementById('originalUrlError');
const customAliasError = document.getElementById('customAliasError');

const shortAliasPattern = /^[A-Za-z0-9_-]+$/;

function setFieldError(element, message) {
  element.textContent = message;
}

function clearStatus() {
  statusMessage.className = 'status-message';
  statusMessage.textContent = '';
}

function showStatus(type, text) {
  statusMessage.className = `status-message ${type}`;
  statusMessage.textContent = text;
}

function validateUrl(url) {
  try {
    const parsed = new URL(url);
    return ['http:', 'https:'].includes(parsed.protocol);
  } catch {
    return false;
  }
}

function validateAlias(alias) {
  if (!alias) {
    return 'Short name is required.';
  }

  const cleaned = alias.trim();
  if (cleaned.length < 3) {
    return 'Short name must be at least 3 characters long.';
  }

  if (!shortAliasPattern.test(cleaned)) {
    return 'Short name may only contain letters, numbers, hyphen, or underscore.';
  }

  return '';
}

function updateSubmitState(isLoading) {
  submitButton.disabled = isLoading;
  const buttonText = submitButton.querySelector('.button-text');
  const spinner = submitButton.querySelector('.spinner');

  buttonText.hidden = isLoading;
  spinner.hidden = !isLoading;
}

function setGeneratedUrl(url) {
  shortenedUrlInput.value = url;
  shortenedUrlLink.href = url;

  try {
    const shortName = new URL(url).pathname.split('/').filter(Boolean).pop() || '';
    shortenedUrlLink.textContent = shortName;
  } catch {
    shortenedUrlLink.textContent = url;
  }

  shortenedUrlLink.hidden = !url;
  copyButton.disabled = !url;
}

async function createShortLink(event) {
  event.preventDefault();
  clearStatus();

  const originalUrl = originalUrlInput.value.trim();
  const customAlias = customAliasInput.value.trim();

  let isValid = true;

  if (!originalUrl) {
    setFieldError(originalUrlError, 'Please provide a valid URL.');
    isValid = false;
  } else if (!validateUrl(originalUrl)) {
    setFieldError(originalUrlError, 'Please enter a valid http or https URL.');
    isValid = false;
  } else {
    setFieldError(originalUrlError, '');
  }

  const aliasMessage = validateAlias(customAlias);
  if (aliasMessage) {
    setFieldError(customAliasError, aliasMessage);
    isValid = false;
  } else {
    setFieldError(customAliasError, '');
  }

  if (!isValid) {
    return;
  }

  updateSubmitState(true);

  try {
    const response = await fetch('/api/v1/links', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        original_url: originalUrl,
        custom_alias: customAlias,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      const message = data?.detail || 'Unable to create short link.';
      showStatus('error', message);
      return;
    }

    setGeneratedUrl(data.short_url);
    showStatus('success', 'Short link created successfully!');
  } catch (error) {
    showStatus('error', 'Something went wrong while creating the short link. Please try again.');
  } finally {
    updateSubmitState(false);
  }
}

copyButton.addEventListener('click', async () => {
  const url = shortenedUrlInput.value.trim();
  if (!url) {
    return;
  }

  try {
    await navigator.clipboard.writeText(url);
    copyButton.textContent = 'Copied!';
    setTimeout(() => {
      copyButton.textContent = 'Copy Link';
    }, 1200);
  } catch (error) {
    showStatus('error', 'Unable to copy the short URL. Please copy it manually.');
  }
});

form.addEventListener('submit', createShortLink);
