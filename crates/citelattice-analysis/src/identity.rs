use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::{
    AnalysisError, AnalysisResult, CitationRequest, ExportPermission, ImplementationIdentity,
    METHOD_ID, METHOD_VERSION, RenderSpec, RunIdentity, validate,
};

pub(crate) fn fingerprint<T: Serialize>(
    domain: &str,
    payload: &T,
) -> Result<String, AnalysisError> {
    #[derive(Serialize)]
    struct Framed<'a, T> {
        domain: &'a str,
        payload: &'a T,
    }
    let bytes = serde_json_canonicalizer::to_vec(&Framed { domain, payload })
        .map_err(|_| AnalysisError::Encoding)?;
    let digest = Sha256::digest(bytes);
    Ok(hex::encode(digest))
}

pub(crate) fn implementation() -> ImplementationIdentity {
    ImplementationIdentity {
        package: env!("CARGO_PKG_NAME").to_owned(),
        version: env!("CARGO_PKG_VERSION").to_owned(),
        build_revision: option_env!("CITELATTICE_BUILD_REVISION").map(str::to_owned),
    }
}

pub(crate) fn identity(
    request: &CitationRequest,
    implementation: &ImplementationIdentity,
) -> Result<RunIdentity, AnalysisError> {
    #[derive(Serialize)]
    struct Input<'a> {
        source: &'a citelattice_core::contracts::versioning::Revision,
        context: &'a crate::CitationContext,
        observations: &'a [crate::CitationObservation],
    }
    #[derive(Serialize)]
    struct Calculation<'a> {
        input_sha256: &'a str,
        method: &'a str,
        method_version: &'a str,
        implementation: &'a ImplementationIdentity,
        missing: crate::MissingPolicy,
    }
    let input_sha256 = fingerprint(
        "citelattice.input.v1",
        &Input {
            source: &request.source,
            context: &request.context,
            observations: &request.observations,
        },
    )?;
    let calculation_sha256 = fingerprint(
        "citelattice.calculation.v1",
        &Calculation {
            input_sha256: &input_sha256,
            method: METHOD_ID,
            method_version: METHOD_VERSION,
            implementation,
            missing: request.missing,
        },
    )?;
    Ok(RunIdentity {
        input_sha256,
        calculation_sha256,
        request_sha256: fingerprint("citelattice.request.v1", request)?,
    })
}

/// Derive a render-cache key without recalculating the scientific metric.
///
/// # Errors
/// Rejects denied/unknown caller export policy, invalid renderer identity or a
/// modified result. This detects accidental tampering, not adversarial forgery:
/// an unkeyed digest is not a digital signature or independent rights decision.
pub fn render_key(result: &AnalysisResult, spec: &RenderSpec) -> Result<String, AnalysisError> {
    #[derive(Serialize)]
    struct Render<'a> {
        result_sha256: &'a str,
        specification: &'a RenderSpec,
    }
    if result.body.export != ExportPermission::Allowed {
        return Err(AnalysisError::ExportDenied);
    }
    validate::revision(&spec.renderer)?;
    if !validate::digest(&spec.scene_sha256) || !validate::digest(&spec.assets_sha256) {
        return Err(AnalysisError::Metadata);
    }
    if fingerprint("citelattice.result.v1", &result.body)? != result.sha256 {
        return Err(AnalysisError::Integrity);
    }
    fingerprint(
        "citelattice.render.v1",
        &Render {
            result_sha256: &result.sha256,
            specification: spec,
        },
    )
}
