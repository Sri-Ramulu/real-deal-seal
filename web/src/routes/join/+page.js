import { redirect } from '@sveltejs/kit';

// Joining is hidden for the hackathon submission; the page code stays. Delete this file to bring it back.
export function load() {
  redirect(307, '/studio');
}
